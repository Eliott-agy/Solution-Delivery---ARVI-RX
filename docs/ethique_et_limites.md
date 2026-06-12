# Éthique, sécurité et limites
> **Author :** Badr TAJINI 
> **Solution Delivery - filière Data** 
>  **Année académique :** 2025-2026
## Ligne rouge

Ce dépôt est un support pédagogique. Il ne doit pas être utilisé pour poser un diagnostic, trier des patients, recommander un traitement ou remplacer un professionnel qualifié.

## Avertissement obligatoire

> Prototype pédagogique. Non destiné au diagnostic. Validation par un professionnel qualifié requise.

Cet avertissement doit apparaître dans :

- l'interface web ;
- la sortie JSON ;
- le README ;
- la soutenance ;
- le rapport final.

## Données

Utiliser uniquement :

- données synthétiques ;
- datasets publics autorisés ;
- images explicitement dé-identifiées ;
- sous-ensembles documentés par un fichier de métadonnées.

Ne jamais stocker : nom, prénom, date de naissance, identifiant patient réel, centre hospitalier, information clinique personnelle.

## Garde-fous fonctionnels

- Classe `uncertain` si qualité image faible ou signes insuffisants.
- Refus des conclusions définitives.
- Contrôle de validité JSON.
- Limitation de la justification aux observations visibles.
- Journalisation des prompts, modèles, sorties et latences.

## Limites à documenter

- Données synthétiques ou sous-ensembles non représentatifs.
- Risque d'hallucination textuelle.
- Confiance non automatiquement calibrée.
- Sensibilité aux prompts et au modèle choisi.
- Nécessité d'une validation indépendante pour tout usage réel.
