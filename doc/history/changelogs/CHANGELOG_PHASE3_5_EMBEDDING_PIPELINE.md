# Changelog — Phase 3.5 embedding pipeline

## Ajouté

- `src/inference/embedding_pipeline.py`
  - `OpenVINOEmbeddingPipelineConfig`
  - `OpenVINOEmbeddingPipelineResult`
  - `OpenVINOEmbeddingPipeline`
- `tests/inference/test_openvino_embedding_pipeline.py`
- `doc/MODEL_EMBEDDING_PIPELINE_PHASE3_5.md`
- `CHANGELOG_PHASE3_5_EMBEDDING_PIPELINE.md`
- `doc/docs/architecture/inference/47_openvino_embedding_pipeline.dot`

## Modifié

- `src/inference/openvino_runtime.py`
  - expose `raw_outputs` dans `InferenceResult.metadata` pour permettre le post-traitement embedding.
- `src/inference/__init__.py`
  - exporte le pipeline embedding.
- `tests/inference/test_openvino_runtime.py`
  - vérifie la présence de `raw_outputs`.
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/MODEL_TOKENIZER_CONTRACT_PHASE3_4.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/45_openvino_embedding_raw.dot`
- `doc/docs/architecture/inference/46_tokenizer_contract.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Intention

Assembler les contrats OpenVINO embedding existants dans une chaîne abstraite complète, sans choisir d'implémentation concrète de tokenizer, sans Qdrant et sans nouvelle responsabilité dans le Scheduler.

## Validation

```text
compileall OK
pytest OK
main.py OK
DOT_OK
```
