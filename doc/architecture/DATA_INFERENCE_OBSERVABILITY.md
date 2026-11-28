# Données, inférence et observation

## Données et retrieval
PostgreSQL est l'autorité durable. Qdrant est une projection vectorielle de rappel ; ses points restent liés à des références durables et reconstructibles. Le rappel Qdrant doit réhydrater depuis SQL.

OpenVINO et le profil multilingual-e5-small fournissent les embeddings E5 canoniques de 384 dimensions. Toute évolution de modèle/dimension requiert une évolution explicite des contrats/index.

## Contrats hardware
`src/contracts/hardware.py` définit `missipy.hardware_sample.v1` et `missipy.hardware_cell.v1`, unités, références typées, fraîcheur et statut. Ce sont des contrats ; 0288 n'ajoute pas de collecteur OS.

## Observation
EventBus diffuse les événements aux abonnés. Le pont Cell Lens projette certains événements dans un journal append-only ; snapshots/replay et read-models passifs permettent de reconstruire une représentation. `passive_supervisor_visual_read_model.py` est JSON-compatible et ne dépend pas de VisPy : ne pas en déduire un renderer VisPy opérationnel.

Les écritures métier durables passent par les surfaces SQL autorisées ; EventBus et supervision sont passifs ; les mesures physiques ne définissent pas la capacité logique ; inconnu/périmé ne devient jamais zéro.
