# Protocole d'évaluation
> **Author :** Badr TAJINI 
> **Solution Delivery - filière Data** 
>  **Année académique :** 2025-2026
## Jeux de cas

- `smoke` : 20 images pour vérifier la chaîne.
- `dev` : 100 à 150 cas si un vrai dataset est utilisé.
- `final` : 20 à 30 cas commentés pour la soutenance.

Le jeu synthétique fourni sert uniquement à valider le pipeline logiciel : chargement, inférence jouet, JSON, logs, métriques et garde-fous. Un score parfait sur ce jeu ne constitue pas une performance médicale.

## Métriques minimales

- Accuracy.
- Macro-F1.
- Sensibilité sur les cas `suspected_opacity`.
- Spécificité sur les cas `normal`.
- Taux de JSON valide.
- Taux de warning présent.
- Taux d'incertitude.
- Hallucinations textuelles détectées manuellement.
- Latence médiane.

## Taxonomie d'erreurs

| Code | Signification | Exemple |
|---|---|---|
| FN | Faux négatif | anomalie présente prédite normale |
| FP | Faux positif | image normale prédite suspecte |
| UA | Incertitude acceptable | signes faibles ou image limitée |
| JF | JSON format error | sortie non exploitable |
| HT | Hallucination textuelle | mention d'un signe non visible |

## Règle de soutenance

Ne jamais montrer seulement des réussites. Une bonne défense montre aussi les faux positifs, les faux négatifs, les incertitudes et les limites de qualité image.

## Smoke test attendu

Avant toute démonstration, le dépôt doit passer un contrôle court :

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
python eval/run_evaluation.py --mode toy --out-dir /tmp/assistant-radio-eval --db-path /tmp/assistant-radio-evidence.sqlite
```

Ce test ne remplace pas l'analyse d'erreurs. Il vérifie seulement que le dépôt est exécutable, que les avertissements sont présents et que les sorties restent structurées.
