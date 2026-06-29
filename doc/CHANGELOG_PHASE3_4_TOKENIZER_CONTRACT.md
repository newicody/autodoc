# Changelog Phase 3.4 — Tokenizer contract

## Ajouté

- `src/inference/tokenizer_contract.py`
  - `TokenizerConfig`
  - `TokenizationRequest`
  - `TokenizationResult`
  - `TextTokenizer`
  - `TokenizerRegistry`
  - `TokenizerRegistrySnapshot`
- `tests/inference/test_openvino_tokenizer_contract.py`
- `doc/MODEL_TOKENIZER_CONTRACT_PHASE3_4.md`
- `doc/docs/architecture/inference/46_tokenizer_contract.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/OPENVINO_MODEL_STRATEGY.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/45_openvino_embedding_raw.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Notes

Le tokenizer reste abstrait. Aucun import `transformers`, `tokenizers` ou `sentencepiece` n'est ajouté.

Le résultat tokenisé peut être projeté vers `OpenVINOEmbeddingRawInputs`, mais il n'exécute pas OpenVINO et ne choisit aucun modèle.
