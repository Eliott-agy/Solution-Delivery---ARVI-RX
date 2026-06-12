"""
Streamlit demo — Assistant Radiologue Virtuel (EFREI 2025-2026).

Fonctionnalités :
- Upload image + analyse toy ou VLM (Claude API)
- Mode comparaison : baseline vs improved côte à côte
- Sortie JSON téléchargeable
- Dashboard métriques de la dernière évaluation
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference import toy_predict, vlm_predict, compare_predictions
from src.guardrails import apply_safety_guardrails, WARNING_TEXT

# ---------------------------------------------------------------------------
# Config page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Assistant radiologue virtuel",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Bannière non-clinique — obligatoire, toujours visible
st.error(
    "**AVERTISSEMENT** — Prototype pédagogique. Non destiné au diagnostic. "
    "Validation par un professionnel qualifié requise."
)

st.title("Assistant radiologue virtuel — EFREI 2025-2026")
st.caption("Prototype pédagogique · Non clinique · Licence MIT")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")

    inference_mode = st.radio(
        "Moteur d'inférence",
        ["toy (sans API)", "vlm (Claude API)"],
        index=0,
        help=(
            "**toy** : classificateur déterministe basé sur le nom de fichier. "
            "Aucune clé API requise. Reproductible.\n\n"
            "**vlm** : appel Claude multimodal. Nécessite `ANTHROPIC_API_KEY`. "
            "Fallback automatique vers toy si la clé est absente."
        ),
    )
    use_vlm = inference_mode.startswith("vlm")

    if use_vlm:
        api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
        if api_key_set:
            st.success("ANTHROPIC_API_KEY détectée")
        else:
            st.warning("ANTHROPIC_API_KEY non définie — fallback toy actif")

    prompt_mode = st.selectbox(
        "Version du prompt",
        ["baseline", "improved"],
        help=(
            "**baseline** : prompt simple, claude-haiku.\n\n"
            "**improved** : prompt avec protocole d'analyse et confidence gate, claude-sonnet."
        ),
    )

    compare_mode = st.checkbox(
        "Comparer baseline vs improved",
        value=False,
        help="Exécute les deux versions et affiche les résultats côte à côte.",
    )

    st.markdown("---")
    st.markdown("**Classes de sortie**")
    st.markdown("- `normal`")
    st.markdown("- `suspected_opacity`")
    st.markdown("- `uncertain` ← garde-fou")
    st.markdown(f"**Confidence gate** : < {0.60:.0%} → uncertain")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_CLASS_COLOR = {"normal": "green", "suspected_opacity": "orange", "uncertain": "gray"}
_CLASS_FR = {"normal": "NORMAL", "suspected_opacity": "OPACITÉ SUSPECTÉE", "uncertain": "INCERTAIN"}


def _run(image_path: Path, mode: str) -> dict:
    fn = vlm_predict if use_vlm else toy_predict
    return apply_safety_guardrails(fn(image_path, mode=mode))


def _render(result: dict, title: str = "") -> None:
    cls = result.get("predicted_class", "uncertain")
    conf = result.get("confidence", 0.0)
    color = _CLASS_COLOR.get(cls, "gray")

    if title:
        st.markdown(f"#### {title}")

    st.markdown(f"**Classe :** :{color}[**{_CLASS_FR.get(cls, cls.upper())}**]")
    c1, c2 = st.columns(2)
    c1.metric("Confiance", f"{conf:.1%}")
    c2.metric("Qualité image", result.get("image_quality", "—"))

    with st.expander("Observations", expanded=True):
        for obs in result.get("visual_evidence", []):
            st.markdown(f"- {obs}")

    with st.expander("Justification"):
        st.write(result.get("justification", "—"))

    with st.expander("Limites"):
        for lim in result.get("limitations", []):
            st.markdown(f"- {lim}")

    if result.get("guardrail_errors"):
        st.caption(f"Guardrail errors: {result['guardrail_errors']}")

    st.caption(f"Modèle : `{result.get('model_name','—')}` · Latence : {result.get('latency_ms', 0)} ms")


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
st.markdown("---")
uploaded = st.file_uploader(
    "Déposer une radiographie thoracique frontale",
    type=["png", "jpg", "jpeg"],
    help="Images synthétiques disponibles dans data/sample_images/. Aucune donnée patient réelle.",
)

if uploaded:
    suffix = Path(uploaded.name).suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = Path(tmp.name)

    try:
        col_img, col_res = st.columns([1, 2], gap="large")

        with col_img:
            st.image(Image.open(tmp_path), caption=uploaded.name, use_container_width=True)
            st.caption(f"Taille : {len(uploaded.getvalue()) / 1024:.1f} KB")

        with col_res:
            if compare_mode:
                st.subheader("Comparaison Baseline vs Improved")
                cb, ci = st.columns(2)
                with cb:
                    with st.spinner("Baseline…"):
                        r_base = _run(tmp_path, "baseline")
                    _render(r_base, "Baseline")
                with ci:
                    with st.spinner("Improved…"):
                        r_imp = _run(tmp_path, "improved")
                    _render(r_imp, "Improved")

                final = r_imp
                if r_base["predicted_class"] == r_imp["predicted_class"]:
                    st.success(f"Les deux versions s'accordent : **{r_base['predicted_class']}**")
                else:
                    st.warning(
                        f"Désaccord — Baseline : **{r_base['predicted_class']}** / "
                        f"Improved : **{r_imp['predicted_class']}**"
                    )
            else:
                with st.spinner(f"Analyse {prompt_mode}…"):
                    final = _run(tmp_path, prompt_mode)
                _render(final)

        # Warning non-clinique répété — obligatoire
        st.warning(WARNING_TEXT)

        # JSON brut + téléchargement
        st.markdown("---")
        st.subheader("Sortie JSON brute")
        st.json(final)
        st.download_button(
            "Télécharger JSON",
            data=json.dumps(final, ensure_ascii=False, indent=2),
            file_name="prediction.json",
            mime="application/json",
        )

    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

else:
    st.info("Utiliser les images synthétiques dans `data/sample_images/` pour tester le flux.")

# ---------------------------------------------------------------------------
# Dashboard métriques (si résultats d'évaluation disponibles)
# ---------------------------------------------------------------------------
eval_outputs = ROOT / "eval" / "outputs"
metrics_files = sorted(eval_outputs.glob("*_metrics.json"), reverse=True) if eval_outputs.exists() else []

if metrics_files:
    st.markdown("---")
    st.subheader("Dashboard métriques — dernière évaluation")

    tabs = st.tabs([f.stem for f in metrics_files[:4]])
    for tab, mfile in zip(tabs, metrics_files[:4]):
        with tab:
            m = json.loads(mfile.read_text(encoding="utf-8"))
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Accuracy", f"{m.get('accuracy', 0):.1%}")
            c2.metric("Macro F1", f"{m.get('macro_f1', 0):.1%}")
            c3.metric("JSON valide", f"{m.get('json_valid_rate', 0):.1%}")
            c4.metric("Warning rate", f"{m.get('warning_rate', 0):.1%}")
            c5.metric("Uncertain rate", f"{m.get('uncertain_rate', 0):.1%}")
            st.json(m)

    summary_file = eval_outputs / "before_after_summary.csv"
    if summary_file.exists():
        import pandas as pd
        st.subheader("Comparaison baseline vs improved")
        df = pd.read_csv(summary_file)
        st.dataframe(df, use_container_width=True)
else:
    st.info(
        "Aucun résultat d'évaluation. "
        "Lancez : `python eval/run_evaluation.py --mode toy`"
    )
