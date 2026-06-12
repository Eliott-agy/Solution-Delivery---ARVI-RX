# Appel d'offre - Solution Delivery - DATA

**Auteur :** Badr Tajini  
**École :** EFREI - Solution Delivery - Filière Data  
**Année académique :** 2025-2026

## Nom

Assistant radiologue virtuel responsable - prototype pédagogique d'IA multimodale pour l'analyse prudente de radiographies thoraciques.

## Filière

Intelligence artificielle & Data Science / Software Engineering / Santé numérique.

## Thème

IA médicale multimodale, vision-language models et prototype web traçable pour l'aide pédagogique à l'analyse d'images médicales.

## Mots-clés

- IA médicale multimodale
- Radiographie thoracique
- Vision-Language Models

## Problème / défi

Les modèles multimodaux peuvent produire un texte médical convaincant à partir d'une image, mais cette fluidité ne garantit pas la correction clinique. Le défi est donc de concevoir un prototype qui ne se contente pas de répondre : il doit structurer sa sortie, expliciter son incertitude, journaliser ses résultats et permettre une analyse d'erreurs.

Le projet ne vise pas le diagnostic. Il vise l'apprentissage d'une démarche d'ingénierie responsable : périmètre restreint, baseline, métriques, logs, garde-fous, démo web et limites documentées.

## Objectif

Développer une application web qui reçoit une radiographie thoracique frontale et retourne une sortie JSON avec : qualité de l'image, classe prédite (`normal`, `suspected_opacity`, `uncertain`), confiance, observations visuelles, justification courte, limites et avertissement.

La solution devra comparer une baseline par prompting à une amélioration légère : prompt renforcé, vote de prompts, seuil d'incertitude, classifieur auxiliaire ou LoRA expérimental si les ressources le permettent.

## Résultats attendus

- Dépôt GitHub structuré et documenté.
- Baseline reproductible en notebook.
- Comparaison de prompts et version améliorée.
- Démo web avec upload, warning et logs.
- Dashboard / CSV de métriques.
- Registre d'erreurs sur 20 à 30 cas commentés.
- Rapport final expliquant dataset, prompts, limites et risques.

## MUST / SHOULD / COULD

### MUST - socle obligatoire

Application web, dépôt d'image, sortie JSON, trois classes, warning obligatoire, baseline reproductible, logs, CSV de résultats, mini-rapport et analyse minimale des limites.

### SHOULD - niveau attendu

Prompt amélioré, règle d'incertitude, comparaison baseline/amélioration, dashboard de métriques, SQLite, smoke test automatisé et analyse d'erreurs sur cas commentés.

### COULD - approfondissements

LoRA Gemma 4 via Unsloth, adaptation MedGemma via PEFT/QLoRA, localisation visuelle, ablation systématique de prompts ou protocole d'évaluation plus proche d'un contexte réel.

## Références techniques et licences

Les extensions par modèles externes ou datasets réels doivent être traitées comme des dépendances réglementées, pas comme de simples fichiers de démonstration. Le rapport devra citer les sources, versions, licences ou conditions d'accès utilisées.

| Ressource | Usage possible | Référence |
|---|---|---|
| Unsloth - Gemma 4 | Fine-tuning expérimental LoRA/QLoRA | R1, R2, R3 |
| MedGemma | Modèle médical image-texte, sous conditions d'usage spécifiques | R4 |
| MIMIC-CXR / MIMIC-CXR-JPG | Radiographies thoraciques avec accès contrôlé | R5, R6 |
| CheXpert | Radiographies thoraciques et rapports associés | R7 |

- R1 - Unsloth, guide Gemma 4 : https://unsloth.ai/docs/models/gemma-4/train
- R2 - Unsloth, catalogue des modèles : https://unsloth.ai/docs/get-started/unsloth-model-catalog
- R3 - Unsloth, blog : https://unsloth.ai/blog
- R4 - Google MedGemma, model card Hugging Face : https://huggingface.co/google/medgemma-4b-pt
- R5 - PhysioNet, MIMIC-CXR v2.1.0 : https://physionet.org/content/mimic-cxr/2.1.0/
- R6 - PhysioNet, MIMIC-CXR-JPG v2.1.0 : https://physionet.org/content/mimic-cxr-jpg/2.1.0/
- R7 - Stanford AIMI, CheXpert : https://aimi.stanford.edu/datasets/chexpert-chest-x-rays

## Critères d'évaluation

- Périmètre + dataset : 15 %
- Baseline fonctionnelle : 15 %
- Amélioration mesurée : 20 %
- Intégration application : 15 %
- Évaluation + erreurs : 20 %
- Éthique + limites : 10 %
- Oral professionnel : 5 %

## Position finale attendue

Un prototype fiable, prudent et documenté vaut mieux qu'une solution spectaculaire mais impossible à défendre.

La soutenance doit donc montrer des preuves : commandes exécutables, sorties JSON, métriques, erreurs, avertissements et limites. Sans ces preuves, le projet reste une démonstration fragile.
