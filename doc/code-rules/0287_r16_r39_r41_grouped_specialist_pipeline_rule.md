# Règle 0287 r16-r39/r16-r41 — pipeline groupé des spécialistes

- Réutiliser les fonctions métier existantes de visite, SQL et Qdrant.
- Regrouper uniquement les effets qui partagent une frontière de commit claire.
- Conserver deux analyses, deux artefacts SQL et deux projections Qdrant distincts.
- Persister dans PostgreSQL avant toute projection OpenVINO/E5 ou Qdrant.
- Maintenir la dimension E5 à 384.
- Enregistrer explicitement les handlers au bootstrap.
- Réhydrater les résultats précédents par un port injecté et durable.
- Ne créer aucun Scheduler parallèle, manager, daemon, Dispatcher ou EventBus.
- Ne laisser aucun handler choisir la tâche suivante ou la politique de reprise.
- Garder PassiveSupervisor et VisPy observation-only.
