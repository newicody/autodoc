# Autodoc / MissiPy — documentation de référence

Autodoc/MissiPy évolue vers un **automate cellulaire de recherche** : cellules logiques, états, relations, observations et évolution des recherches. Cette documentation est organisée par unités architecturales, pas par numéro de patch.

## Documents de référence
- [Automate cellulaire](architecture/CELLULAR_AUTOMATON.md)
- [Noyau et Scheduler](architecture/KERNEL_AND_SCHEDULER.md)
- [Cadrage scientifique Copilot–serveur](architecture/COPILOT_SCIENTIFIC_FRAMING.md)
- [Recherche et contexte](architecture/RESEARCH_AND_CONTEXT.md)
- [Données, inférence et observation](architecture/DATA_INFERENCE_OBSERVABILITY.md)
- [Dépendances](DEPENDENCIES.md) · [Licences](LICENSES.md) · [Installation](INSTALLATION.md) · [Roadmap](ROADMAP.md)

Graphes fonctionnels Graphviz : [architecture/current](architecture/current/).

## Règles documentaires
Le code de la branche courante est la référence de l'état implémenté. Un contrat ne prouve pas qu'un producteur existe. Les projections d'observation ne commandent pas. PostgreSQL est l'autorité durable ; Qdrant est une projection reconstruisible. Le Scheduler est l'autorité unique d'admission et d'orchestration. Les labs/spécialistes n'ont pas d'orchestrateur parallèle. Les objectifs de roadmap ne sont pas des fonctionnalités livrées.

Les patches, rapports, manifests, roadmaps périmées et anciennes architectures sont conservés dans `history/` à titre informatif. Ils ne sont pas normatifs.

Référence de consolidation : branche `docs/unification-027x`, HEAD audité `adc6343abcb7efd23e8c3cf3658c86c1d337bcbf`. Cette consolidation documentaire ne certifie pas l'installation ou l'exploitation de production.
