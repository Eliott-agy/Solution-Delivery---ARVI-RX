from __future__ import annotations

import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from .preprocessing import basic_quality_flag

logger = logging.getLogger(__name__)

WARNING = "Prototype pédagogique. Non destiné au diagnostic. Validation par un professionnel qualifié requise."

CONFIDENCE_GATE = 0.60  # below this → uncertain (improved mode and VLM)

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def toy_predict(image_path: str | Path, mode: str = "baseline") -> dict[str, Any]:
    """Deterministic toy predictor used to validate the repo pipeline.

    It reads synthetic labels from filenames. This is not medical inference.
    """
    start = time.perf_counter()
    name = Path(image_path).name.lower()
    quality = basic_quality_flag(image_path)

    if "suspected_opacity" in name:
        pred = "suspected_opacity"
        conf = 0.78 if mode == "baseline" else 0.72
        evidence = ["synthetic opacity-like area visible in the lung field"]
        justification = "The synthetic image contains a localized brighter region compatible with the toy opacity class. This is a pipeline validation result, not a medical interpretation."
    elif "normal" in name:
        pred = "normal"
        conf = 0.72 if mode == "baseline" else 0.68
        evidence = ["no synthetic opacity marker detected"]
        justification = "The synthetic image does not contain the opacity marker used by the toy generator. This conclusion is limited to the synthetic validation setting."
    else:
        pred = "uncertain"
        conf = 0.52
        evidence = ["limited synthetic image quality"]
        justification = "The image is treated as limited quality in the toy catalog. The safe output is uncertainty rather than a forced class."

    # Improved mode is more conservative.
    if mode == "improved" and quality != "good":
        pred = "uncertain"
        conf = min(conf, 0.55)

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "image_quality": quality,
        "predicted_class": pred,
        "confidence": round(float(conf), 3),
        "visual_evidence": evidence,
        "justification": justification,
        "limitations": ["synthetic toy image", "no clinical context", "not a validated medical model"],
        "warning": WARNING,
        "model_name": f"toy-rule-{mode}",
        "prompt_version": f"{mode}_v1",
        "latency_ms": latency_ms,
    }


def vlm_predict(image_path: str | Path, mode: str = "baseline") -> dict[str, Any]:
    """Call the Claude multimodal API to analyse a chest X-ray.

    Falls back to toy_predict if ANTHROPIC_API_KEY is not set or if the call fails.
    Keeps the same output schema as toy_predict.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — falling back to toy_predict.")
        result = toy_predict(image_path, mode=mode)
        result["limitations"] = result["limitations"] + ["fallback to toy: ANTHROPIC_API_KEY not set"]
        return result

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed — falling back to toy_predict.")
        result = toy_predict(image_path, mode=mode)
        result["limitations"] = result["limitations"] + ["fallback to toy: anthropic package missing"]
        return result

    prompt_file = _PROMPTS_DIR / f"{mode}_prompt.txt"
    if not prompt_file.exists():
        logger.warning("Prompt file missing: %s — falling back to toy_predict.", prompt_file)
        return toy_predict(image_path, mode=mode)

    prompt_text = prompt_file.read_text(encoding="utf-8")
    model_name = "claude-haiku-4-5-20251001" if mode == "baseline" else "claude-sonnet-4-6"

    start = time.perf_counter()
    try:
        image_data, media_type = _encode_image(image_path)
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": prompt_text},
                ],
            }],
        )
        raw = response.content[0].text
        result = _parse_vlm_response(raw, mode, model_name)
    except Exception as exc:
        logger.error("Claude API call failed (%s): %s — falling back to toy_predict.", type(exc).__name__, exc)
        result = toy_predict(image_path, mode=mode)
        result["limitations"] = result["limitations"] + [f"fallback to toy: API error ({type(exc).__name__})"]
        return result

    latency_ms = int((time.perf_counter() - start) * 1000)
    result["latency_ms"] = latency_ms
    result["image_quality"] = result.get("image_quality") or basic_quality_flag(image_path)

    # Confidence gate: improved prompt requires conf >= 0.60 or → uncertain
    if mode == "improved":
        try:
            if float(result.get("confidence", 0)) < CONFIDENCE_GATE:
                result["predicted_class"] = "uncertain"
                result.setdefault("limitations", [])
                if "confidence below threshold" not in str(result["limitations"]):
                    result["limitations"] = list(result["limitations"]) + [
                        f"confidence below threshold {CONFIDENCE_GATE} — class set to uncertain"
                    ]
        except (TypeError, ValueError):
            result["predicted_class"] = "uncertain"

    return result


def _encode_image(image_path: str | Path) -> tuple[str, str]:
    suffix = Path(image_path).suffix.lower()
    media_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".bmp": "image/bmp"}
    media_type = media_map.get(suffix, "image/png")
    data = base64.standard_b64encode(Path(image_path).read_bytes()).decode("utf-8")
    return data, media_type


def _parse_vlm_response(raw: str, mode: str, model_name: str) -> dict[str, Any]:
    """Extract JSON from the VLM response and normalise to the project schema."""
    parsed: dict[str, Any] = {}

    # Try direct parse, then extract JSON block
    for candidate in (raw.strip(), raw[raw.find("{"):raw.rfind("}") + 1] if "{" in raw else ""):
        try:
            parsed = json.loads(candidate)
            break
        except (json.JSONDecodeError, ValueError):
            continue

    if not parsed:
        logger.warning("Could not parse VLM JSON response — returning uncertain.")
        parsed = {
            "image_quality": "unknown",
            "predicted_class": "uncertain",
            "confidence": 0.0,
            "visual_evidence": ["JSON parsing failed — model response was not valid JSON."],
            "justification": "The model response could not be parsed. Uncertain is returned as a safe default.",
            "limitations": ["json parse error", "not a validated medical model"],
        }

    # Normalise schema — the VLM may use slightly different key names
    parsed.setdefault("image_quality", "unknown")
    parsed.setdefault("predicted_class", "uncertain")
    parsed.setdefault("visual_evidence", parsed.pop("visual_observations", ["no observations returned"]))
    parsed.setdefault("limitations", parsed.pop("limits", ["not a validated medical model"]))
    if "not a validated medical model" not in str(parsed["limitations"]):
        parsed["limitations"] = list(parsed["limitations"]) + ["not a validated medical model"]
    parsed["warning"] = WARNING
    parsed["model_name"] = model_name
    parsed["prompt_version"] = f"{mode}_v1"

    # Clamp confidence
    try:
        conf = float(parsed.get("confidence", 0.0))
        parsed["confidence"] = round(max(0.0, min(1.0, conf)), 3)
    except (TypeError, ValueError):
        parsed["confidence"] = 0.0

    # Validate class
    if parsed["predicted_class"] not in {"normal", "suspected_opacity", "uncertain"}:
        parsed["predicted_class"] = "uncertain"

    return parsed


def vlm_predict_placeholder(image_path: str | Path, prompt: str) -> dict[str, Any]:
    """Backward-compatible shim — routes to vlm_predict (with API) or toy_predict.

    Students should keep the same output schema as toy_predict.
    """
    return vlm_predict(image_path, mode="baseline")


def compare_predictions(image_path: str | Path, use_vlm: bool = False) -> dict[str, Any]:
    """Run both baseline and improved on the same image and return a comparison dict."""
    predict_fn = vlm_predict if use_vlm else toy_predict
    start = time.perf_counter()
    baseline = predict_fn(image_path, mode="baseline")
    improved = predict_fn(image_path, mode="improved")
    return {
        "baseline": baseline,
        "improved": improved,
        "agreement": baseline["predicted_class"] == improved["predicted_class"],
        "total_latency_ms": int((time.perf_counter() - start) * 1000),
    }
