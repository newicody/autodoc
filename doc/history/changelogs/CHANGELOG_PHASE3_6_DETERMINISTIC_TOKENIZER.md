# Changelog — Phase 3.6 deterministic tokenizer

## Ajouté

- `src/inference/simple_tokenizer.py`
  - `DeterministicTokenizer`
  - `register_deterministic_test_tokenizer`
- `tests/inference/test_deterministic_tokenizer.py`
- `doc/MODEL_DETERMINISTIC_TOKENIZER_PHASE3_6.md`
- `doc/docs/architecture/inference/48_deterministic_tokenizer.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/46_tokenizer_contract.dot`
- `doc/docs/architecture/inference/47_openvino_embedding_pipeline.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Décision

Le tokenizer ajouté est un outil de test déterministe, pas un tokenizer de
production. Il valide la structure du pipeline sans choisir un vrai modèle.

## Exclusions

- aucun tokenizer Hugging Face ;
- aucune dépendance externe ;
- aucun modèle OpenVINO local ;
- aucun Qdrant ;
- aucun changement Scheduler.
