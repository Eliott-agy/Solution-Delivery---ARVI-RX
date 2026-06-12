# Données

Ce dossier contient un jeu **synthétique jouet** destiné à tester l'architecture, les logs, les métriques et l'interface. Il ne s'agit pas d'un dataset médical réel.

Pour un vrai projet, utiliser un dataset autorisé comme RSNA Pneumonia, CheXpert, MIMIC-CXR ou NIH ChestXray, en respectant les licences et les conditions d'accès.

## `synthetic_cases.csv`

Colonnes :

- `case_id`
- `image_path`
- `source`
- `label`
- `split`
- `quality`
- `notes`

## Images synthétiques

Les images dans `sample_images/` imitent grossièrement une radiographie thoracique uniquement pour vérifier les flux de code. Elles ne doivent pas être utilisées pour évaluer une performance médicale.
