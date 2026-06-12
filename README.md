# Assistant radiologue virtuel responsable

> **Auteur :** Badr Tajini  
> **Solution Delivery - Filière Data**  
> **École :** EFREI  
> **Année académique :** 2025-2026

## Contexte

Prototype pédagogique d'IA médicale multimodale pour apprendre à construire une chaîne **prudente, traçable et évaluée** autour d'une radiographie thoracique frontale.

---

>  **Position non clinique.** Ce dépôt n'est pas un dispositif médical. Il ne doit jamais être utilisé pour diagnostiquer, trier ou orienter un patient. Toute sortie doit rester un résultat expérimental, vérifié par un professionnel qualifié.

---

## Contrat du projet

| Élément | Cadrage |
|---|---|
| Entrée | Une radiographie thoracique frontale |
| Sorties | `normal`, `suspected_opacity`, `uncertain` |
| Preuve minimale | JSON valide, warning, logs, métriques, cas d'erreur |
| Données | Synthétiques ou publiques, autorisées et dé-identifiées |
| Finalité | Prototype éducatif de data/IA, pas aide au diagnostic réelle |

Le bon rendu ne cherche pas à impressionner par un modèle spectaculaire. Il démontre une méthode : périmètre limité, baseline reproductible, garde-fous, évaluation, analyse d'erreurs et limites explicites.

## Démarrage rapide

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python eval/run_evaluation.py --mode toy
streamlit run app/streamlit_app.py
```

## Smoke test du dépôt

Avant une soutenance, un push ou une livraison, lancer le contrôle court :

```bash
pip install -r requirements-test.txt
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
python -m compileall -q src api app eval finetuning tests
python eval/run_evaluation.py --mode toy \
  --out-dir /tmp/assistant-radio-eval \
  --db-path /tmp/assistant-radio-evidence.sqlite
```

Ce smoke test vérifie la structure du dépôt, le contrat du dataset synthétique, le schéma de sortie, les garde-fous, l'API de démonstration, la compilation Python et l'évaluation jouet.

## API de démonstration

```bash
uvicorn api.main:app --reload
```

Exemple :

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -F "file=@data/sample_images/CXR_SYN_002_suspected_opacity.png"
```

La réponse doit contenir une classe, une confiance, des observations visuelles, une justification, des limites et l'avertissement non clinique.

## Organisation

```text
assistant-radiologue-virtuel/
├── README.md
├── docs/          # appel d'offre, architecture, éthique, évaluation
├── data/          # cas synthétiques et images jouet
├── prompts/       # prompt baseline, prompt amélioré, schéma JSON
├── src/           # inférence jouet, garde-fous, métriques, SQLite
├── api/           # FastAPI
├── app/           # Streamlit / Gradio
├── eval/          # évaluation, sorties CSV/JSON, registre d'erreurs
├── tests/         # smoke tests et contrat minimal
├── notebooks/     # notebooks de démarrage
└── finetuning/    # stubs expérimentaux, non obligatoires
```

## Livrables attendus

| Niveau | Attendu |
|---|---|
| **MUST** | Baseline reproductible, sortie JSON valide, warning obligatoire, logs, métriques, mini-rapport |
| **SHOULD** | Prompt amélioré, règle d'incertitude, comparaison baseline/amélioration, analyse d'erreurs |
| **COULD** | LoRA expérimental, MedGemma/PEFT, localisation visuelle, ablations de prompts |

## Références techniques

Les pistes avancées doivent rester expérimentales, traçables et justifiées. En particulier, un groupe qui mobilise Gemma, MedGemma, Unsloth, MIMIC-CXR ou CheXpert doit citer la source exacte, la version, les conditions d'accès et les limites d'usage.

| Ressource | Usage possible | Référence à citer |
|---|---|---|
| Unsloth - Gemma 4 | Fine-tuning LoRA/QLoRA expérimental, uniquement après une baseline simple | [Guide Gemma 4](https://unsloth.ai/docs/models/gemma-4/train), [catalogue des modèles](https://unsloth.ai/docs/get-started/unsloth-model-catalog), [blog Unsloth](https://unsloth.ai/blog) |
| MedGemma | Baseline ou adaptation médicale image-texte, avec prudence sur les conditions d'accès | [Model card Hugging Face](https://huggingface.co/google/medgemma-4b-pt) |
| MIMIC-CXR / MIMIC-CXR-JPG | Jeu de données de radiographies thoraciques, accès contrôlé et non redistribuable | [MIMIC-CXR](https://physionet.org/content/mimic-cxr/2.1.0/), [MIMIC-CXR-JPG](https://physionet.org/content/mimic-cxr-jpg/2.1.0/) |
| CheXpert | Jeu de données public de radiographies thoraciques avec rapports associés | [Stanford AIMI - CheXpert](https://aimi.stanford.edu/datasets/chexpert-chest-x-rays) |

## Points de vigilance

- Ne pas inventer d'information clinique absente de l'image.
- Ne pas supprimer la classe `uncertain`; elle est un garde-fou, pas un échec.
- Ne pas afficher uniquement des réussites en soutenance.
- Ne jamais commiter de données patient réelles, identifiantes ou ambiguës.
- Ne pas présenter le prototype comme validé médicalement.

## Licence et sources externes

Le code pédagogique du dépôt est publié sous licence MIT. **Les datasets externes, modèles et bibliothèques utilisés conservent leurs licences propres** : les étudiants doivent vérifier et documenter les droits d'usage avant toute expérimentation.

Exigence minimale : indiquer dans le rapport la source, la version, la licence ou les conditions d'accès, les restrictions de redistribution, les traitements d'anonymisation et les limites d'interprétation. Aucun fichier patient réel, même pseudonymisé, ne doit être ajouté au dépôt sans autorisation explicite et traçable.
