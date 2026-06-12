from __future__ import annotations

from typing import Any

ALLOWED_CLASSES = {"normal", "suspected_opacity", "uncertain"}
REQUIRED_KEYS = {"image_quality", "predicted_class", "confidence", "visual_evidence", "justification", "limitations", "warning"}
WARNING_TEXT = "Prototype pédagogique. Non destiné au diagnostic. Validation par un professionnel qualifié requise."

# Below this threshold → predicted_class is forced to "uncertain" regardless of model output.
CONFIDENCE_GATE = 0.60


def validate_prediction(pred: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (is_valid, list_of_errors). Does NOT modify pred."""
    errors: list[str] = []
    missing = REQUIRED_KEYS - set(pred)
    if missing:
        errors.append(f"missing keys: {sorted(missing)}")
    if pred.get("predicted_class") not in ALLOWED_CLASSES:
        errors.append("invalid predicted_class")
    try:
        conf = float(pred.get("confidence", -1))
        if not 0 <= conf <= 1:
            errors.append("confidence outside [0,1]")
    except Exception:
        errors.append("confidence is not numeric")
    if not pred.get("warning"):
        errors.append("warning missing")
    return not errors, errors


def apply_safety_guardrails(pred: dict[str, Any]) -> dict[str, Any]:
    """Apply all safety rules in order and return the patched prediction dict.

    Rules (applied in order):
    1. Schema validation — missing keys or invalid class → uncertain + confidence ≤ 0.5.
    2. Image-quality gate — limited/poor quality AND confidence < 0.6 → uncertain.
    3. Confidence gate — any mode with confidence < CONFIDENCE_GATE → uncertain.
    4. Warning injection — always overwritten with the canonical WARNING_TEXT.
    """
    valid, errors = validate_prediction(pred)

    # Rule 1: schema
    if not valid:
        pred["predicted_class"] = "uncertain"
        pred["confidence"] = min(float(pred.get("confidence", 0.0) or 0.0), 0.5)
        pred.setdefault("limitations", []).append("guardrail triggered: invalid output schema")

    # Rule 2: image quality
    try:
        conf = float(pred.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
        pred["confidence"] = 0.0

    if pred.get("image_quality") in {"limited", "poor"} and conf < CONFIDENCE_GATE:
        pred["predicted_class"] = "uncertain"
        pred.setdefault("limitations", []).append(
            f"guardrail: image quality '{pred['image_quality']}' with confidence {conf:.2f} < {CONFIDENCE_GATE}"
        )

    # Rule 3: confidence gate (applies to VLM outputs; toy_predict already handles this internally)
    if conf < CONFIDENCE_GATE and pred.get("predicted_class") != "uncertain":
        pred["predicted_class"] = "uncertain"
        pred.setdefault("limitations", []).append(
            f"guardrail: confidence {conf:.2f} below gate {CONFIDENCE_GATE} — class forced to uncertain"
        )

    # Rule 4: warning — always canonical, non-overridable
    pred["warning"] = WARNING_TEXT
    pred["guardrail_errors"] = errors
    return pred
