# Changelog — Phase 3.3 — Embedding raw IO

## Ajouté

- `src/inference/embedding_raw.py`
  - `OpenVINOEmbeddingRawInputs`
  - `OpenVINOEmbeddingOutputConfig`
  - `OpenVINOEmbeddingOutputAdapter`
  - `OpenVINOEmbeddingVector`
- `tests/inference/test_openvino_embedding_raw.py`
- `doc/MODEL_EMBEDDING_RAW_PHASE3_3.md`
- `doc/docs/architecture/inference/45_openvino_embedding_raw.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/MODEL_EMBEDDING_PROFILE_PHASE3_2.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/44_openvino_embedding_profile.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Intention

Préparer la chaîne embedding raw sans choisir de tokenizer ou de modèle local.

Le runtime OpenVINO réel reste générique. Cette phase ajoute seulement le contrat qui transforme des tokens déjà préparés en `InferenceRequest.context["inputs"]`, puis une sortie brute en vecteur embedding stable.

## Non ajouté

- Pas de tokenizer.
- Pas de Qdrant.
- Pas de dépendance NumPy.
- Pas de modèle BGE-M3, E5 ou MiniLM imposé.
- Pas de modification du Scheduler.
