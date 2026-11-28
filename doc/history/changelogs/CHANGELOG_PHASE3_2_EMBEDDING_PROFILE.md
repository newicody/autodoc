# Changelog Phase 3.2 — Profil embedding configurable

## Objectif

Ajouter un profil `openvino.embedding` configurable sans imposer de modèle local,
sans tokenizer et sans charger OpenVINO automatiquement.

Cette phase prépare le premier type de modèle recommandé pour le prototype :
l'embedding. Le choix exact du modèle reste externe à la configuration du dépôt.

## Ajouté

- `src/inference/embedding_profile.py`
  - `OpenVINOEmbeddingProfileConfig`
  - `SUPPORTED_EMBEDDING_POOLING`
  - `DEFAULT_EMBEDDING_INPUT_NAMES`
  - `DEFAULT_EMBEDDING_OUTPUT_NAMES`
  - `register_openvino_embedding_profile()`
- `tests/inference/test_openvino_embedding_profile.py`
- `doc/MODEL_EMBEDDING_PROFILE_PHASE3_2.md`
- `doc/docs/architecture/inference/44_openvino_embedding_profile.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/MODEL_PROFILES_PHASE3_0.md`
- `doc/MODEL_FACTORY_PHASE3_1.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/43_openvino_profiles.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Décision

Le profil embedding est déclaratif :

```text
OpenVINOEmbeddingProfileConfig
  -> OpenVINOModelProfile(task="embedding")
  -> OpenVINOBackendFactory
  -> OpenVINOBackend
```

Le code ne vérifie pas l'existence du chemin modèle. C'est volontaire : le dépôt
ne doit pas dépendre d'un modèle local précis.

## Non ajouté volontairement

- pas de tokenizer ;
- pas de post-processing vectoriel ;
- pas de Qdrant ;
- pas de modèle BGE-M3 imposé ;
- pas de chemin `/models/...` en dur ;
- pas de modification Scheduler.
