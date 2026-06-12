"""
Evaluation pipeline — Assistant Radiologue Virtuel (EFREI 2025-2026).

Usage:
    # Smoke test (toy, no API key required)
    python eval/run_evaluation.py --mode toy

    # Avec dossiers personnalisés (smoke test CI)
    python eval/run_evaluation.py --mode toy \\
        --out-dir /tmp/assistant-radio-eval \\
        --db-path /tmp/assistant-radio-evidence.sqlite

    # Mode VLM réel (nécessite ANTHROPIC_API_KEY)
    python eval/run_evaluation.py --mode baseline --vlm
    python eval/run_evaluation.py --mode improved --vlm

    # Comparaison complète avec registre d'erreurs
    python eval/run_evaluation.py --mode toy --error-register
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.inference import toy_predict, vlm_predict
from src.guardrails import apply_safety_guardrails, validate_prediction
from src.metrics import summarize_metrics
from src.database import insert_run, init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Taxonomie d'erreurs selon le protocole d'évaluation du prof
ERROR_TAXONOMY = {
    "FN": "Faux négatif — anomalie présente prédite normale",
    "FP": "Faux positif — image normale prédite suspecte",
    "UA": "Incertitude acceptable — signes faibles ou image limitée",
    "JF": "JSON format error — sortie non exploitable",
    "HT": "Hallucination textuelle — mention d'un signe non visible",
}


def read_cases(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def classify_error(label: str, predicted: str, quality: str) -> str:
    """Assign an error code from the taxonomy."""
    if label == predicted:
        return "OK"
    if label == "suspected_opacity" and predicted == "normal":
        return "FN"
    if label == "normal" and predicted == "suspected_opacity":
        return "FP"
    if predicted == "uncertain" and quality in ("limited", "poor"):
        return "UA"
    return "UA"


def run(mode: str, db_path: Path, use_vlm: bool = False) -> tuple[list[dict], dict]:
    """Run inference on all synthetic cases and return (rows, metrics)."""
    cases = read_cases(ROOT / "data" / "synthetic_cases.csv")
    predict_fn = vlm_predict if use_vlm else toy_predict

    rows = []
    init_db(db_path)

    for case in cases:
        image_path = ROOT / case["image_path"]
        pred = apply_safety_guardrails(predict_fn(image_path, mode=mode))
        valid, errors = validate_prediction(pred)

        error_code = classify_error(
            label=case["label"],
            predicted=pred["predicted_class"],
            quality=pred.get("image_quality", "good"),
        )

        row = {
            "case_id": case["case_id"],
            "label": case["label"],
            "predicted_class": pred["predicted_class"],
            "confidence": pred["confidence"],
            "image_quality": pred.get("image_quality", ""),
            "json_valid": valid,
            "warning": pred.get("warning", ""),
            "latency_ms": pred.get("latency_ms", 0),
            "error_code": error_code,
            "guardrail_errors": ";".join(errors),
            "model_name": pred.get("model_name", ""),
        }
        rows.append(row)
        insert_run(db_path, case["case_id"], str(image_path), pred)
        logger.info(
            "[%s] %s — GT=%-20s PRED=%-20s CONF=%.2f",
            error_code,
            case["case_id"],
            case["label"],
            pred["predicted_class"],
            pred["confidence"],
        )

    metrics = summarize_metrics(rows)
    return rows, metrics


def build_error_register(rows_baseline: list[dict], rows_improved: list[dict]) -> list[dict]:
    """Build the commented error register comparing both modes."""
    register = []
    by_id_imp = {r["case_id"]: r for r in rows_improved}

    for r in rows_baseline:
        cid = r["case_id"]
        r_imp = by_id_imp.get(cid, {})

        status_b = r["error_code"]
        status_i = r_imp.get("error_code", "—")

        comment = ""
        if status_b == "OK" and status_i == "OK":
            comment = "Les deux modes classifient correctement."
        elif status_b == "OK" and status_i != "OK":
            comment = f"Régression : baseline correcte, improved produit {status_i}."
        elif status_b != "OK" and status_i == "OK":
            comment = f"Amélioration : baseline produit {status_b}, improved correcte."
        elif status_b == "UA" or status_i == "UA":
            comment = "Cas incertain acceptable — image de qualité limitée."
        else:
            comment = f"Erreur persistante : baseline={status_b}, improved={status_i}."

        register.append({
            "case_id": cid,
            "ground_truth": r["label"],
            "baseline_pred": r["predicted_class"],
            "baseline_conf": r["confidence"],
            "baseline_error": status_b,
            "improved_pred": r_imp.get("predicted_class", "—"),
            "improved_conf": r_imp.get("confidence", "—"),
            "improved_error": status_i,
            "comment": comment,
        })

    return register


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the radiology assistant.")
    parser.add_argument("--mode", choices=["toy", "baseline", "improved"], default="toy",
                        help="'toy' runs both baseline and improved; others run a single mode.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "eval" / "outputs")
    parser.add_argument("--db-path", type=Path, default=ROOT / "medical_ai_evidence.sqlite")
    parser.add_argument("--vlm", action="store_true",
                        help="Use VLM (Claude API) instead of toy predictor.")
    parser.add_argument("--error-register", action="store_true",
                        help="Generate the commented error register CSV + JSON.")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    modes = ["baseline", "improved"] if args.mode == "toy" else [args.mode]
    summary = []
    all_rows: dict[str, list[dict]] = {}

    for mode in modes:
        rows, metrics = run(mode, args.db_path, use_vlm=args.vlm)
        all_rows[mode] = rows
        write_csv(out_dir / f"{mode}_predictions.csv", rows)
        (out_dir / f"{mode}_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        summary.append({"mode": mode, **metrics})
        logger.info("Mode %s — accuracy=%.1f%% macro_f1=%.1f%%",
                    mode, metrics["accuracy"] * 100, metrics["macro_f1"] * 100)

    write_csv(out_dir / "before_after_summary.csv", summary)

    # Error register (SHOULD level)
    if args.error_register and "baseline" in all_rows and "improved" in all_rows:
        register = build_error_register(all_rows["baseline"], all_rows["improved"])
        write_csv(out_dir / "error_register.csv", register)
        (out_dir / "error_register.json").write_text(
            json.dumps({"taxonomy": ERROR_TAXONOMY, "cases": register}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Registre d'erreurs sauvegardé : %s", out_dir / "error_register.json")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
