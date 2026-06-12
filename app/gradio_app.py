from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference import toy_predict, vlm_predict
from src.guardrails import apply_safety_guardrails, WARNING_TEXT

_NON_CLINICAL = (
    "AVERTISSEMENT — Prototype pédagogique. Non destiné au diagnostic. "
    "Validation par un professionnel qualifié requise."
)

_CLASS_EMOJI = {
    "normal": "🟢 NORMAL",
    "suspected_opacity": "🟠 OPACITÉ SUSPECTÉE",
    "uncertain": "⚪ INCERTAIN",
}


def _predict(image_path: str | None, mode: str, use_vlm: bool) -> tuple[str, str]:
    if image_path is None:
        return "Aucune image fournie.", "{}"

    predict_fn = vlm_predict if use_vlm else toy_predict
    pred = apply_safety_guardrails(predict_fn(image_path, mode=mode))

    cls   = pred.get("predicted_class", "uncertain")
    conf  = pred.get("confidence", 0.0)
    qual  = pred.get("image_quality", "—")
    ev    = "\n".join(f"• {e}" for e in pred.get("visual_evidence", []))
    just  = pred.get("justification", "—")
    lims  = "\n".join(f"• {l}" for l in pred.get("limitations", []))
    model = pred.get("model_name", "—")
    lat   = pred.get("latency_ms", 0)

    summary = (
        f"**Classe :** {_CLASS_EMOJI.get(cls, cls.upper())}\n\n"
        f"**Confiance :** {conf:.1%}  |  **Qualité image :** {qual}\n\n"
        f"**Observations visuelles :**\n{ev}\n\n"
        f"**Justification :**\n{just}\n\n"
        f"**Limites :**\n{lims}\n\n"
        f"---\n*Modèle : `{model}` · Latence : {lat} ms*\n\n"
        f"⚠️ *{WARNING_TEXT}*"
    )
    return summary, json.dumps(pred, ensure_ascii=False, indent=2)


def _compare(image_path: str | None, use_vlm: bool) -> tuple[str, str, str]:
    if image_path is None:
        return "Aucune image fournie.", "—", "{}"

    predict_fn = vlm_predict if use_vlm else toy_predict
    pred_b = apply_safety_guardrails(predict_fn(image_path, mode="baseline"))
    pred_i = apply_safety_guardrails(predict_fn(image_path, mode="improved"))

    def row(pred: dict, label: str) -> str:
        cls  = pred.get("predicted_class", "uncertain")
        conf = pred.get("confidence", 0.0)
        return f"**{label}** → {_CLASS_EMOJI.get(cls, cls)} ({conf:.1%})"

    agreement = pred_b["predicted_class"] == pred_i["predicted_class"]
    status    = "✅ Accord" if agreement else "⚠️ Désaccord"

    result = f"{row(pred_b, 'Baseline')}\n\n{row(pred_i, 'Improved')}\n\n{status}"
    raw    = json.dumps({"baseline": pred_b, "improved": pred_i, "agreement": agreement},
                        ensure_ascii=False, indent=2)
    return result, f"⚠️ *{WARNING_TEXT}*", raw


# -------------------------------------------------------------------
# Interface 1 — Analyse simple
# -------------------------------------------------------------------
with gr.Blocks(title="Assistant radiologue virtuel") as demo_single:
    gr.Markdown(f"## Assistant radiologue virtuel — EFREI 2025-2026\n\n> ⚠️ **{_NON_CLINICAL}**")

    with gr.Row():
        img_input = gr.Image(type="filepath", label="Radiographie thoracique frontale")
        with gr.Column():
            mode_sel   = gr.Radio(["baseline", "improved"], value="baseline", label="Version du prompt")
            vlm_toggle = gr.Checkbox(
                value=False,
                label="Utiliser VLM (Claude API)",
                info="Nécessite ANTHROPIC_API_KEY. Fallback automatique vers toy si absente.",
            )
            run_btn = gr.Button("Analyser", variant="primary")

    with gr.Row():
        summary_out = gr.Markdown(label="Résultat")
        json_out    = gr.Code(language="json", label="JSON brut")

    run_btn.click(fn=_predict, inputs=[img_input, mode_sel, vlm_toggle], outputs=[summary_out, json_out])


# -------------------------------------------------------------------
# Interface 2 — Comparaison baseline vs improved
# -------------------------------------------------------------------
with gr.Blocks(title="Comparaison prompts") as demo_compare:
    gr.Markdown(f"## Comparaison Baseline vs Improved\n\n> ⚠️ **{_NON_CLINICAL}**")

    with gr.Row():
        img2       = gr.Image(type="filepath", label="Radiographie thoracique frontale")
        vlm_toggle2 = gr.Checkbox(value=False, label="Utiliser VLM (Claude API)")
        cmp_btn     = gr.Button("Comparer", variant="primary")

    cmp_result  = gr.Markdown(label="Comparaison")
    cmp_warning = gr.Markdown()
    cmp_json    = gr.Code(language="json", label="JSON brut")

    cmp_btn.click(fn=_compare, inputs=[img2, vlm_toggle2], outputs=[cmp_result, cmp_warning, cmp_json])


# -------------------------------------------------------------------
# Tabs app (main entry point)
# -------------------------------------------------------------------
demo = gr.TabbedInterface(
    [demo_single, demo_compare],
    ["Analyse", "Comparaison"],
    title="Assistant radiologue virtuel",
)

if __name__ == "__main__":
    print(f"API key définie : {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
    demo.launch()
