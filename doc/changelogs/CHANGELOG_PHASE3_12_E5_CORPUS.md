# Changelog — Phase 3.12 E5 corpus local

## Ajouté

- `src/inference/e5_corpus.py`
  - `E5CorpusDocument`
  - `E5CorpusEmbedding`
  - `E5CorpusIndex`
  - `E5CorpusBuilder`
  - `E5CorpusSearcher`
  - `E5CorpusSearchHit`
  - `E5CorpusSearchResults`
  - `E5CorpusJsonStore`
  - `make_corpus_document_id()`
- `src/inference/e5_corpus_cli.py`
- `tools/build_e5_corpus.py`
- `tools/search_e5_corpus.py`
- `tests/inference/test_e5_corpus.py`
- `tests/inference/test_e5_corpus_cli.py`
- `doc/MODEL_E5_CORPUS_PHASE3_12.md`
- `doc/docs/architecture/inference/50_e5_corpus.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Décision

Le corpus local sert de transition entre le ranking direct et Qdrant. Les passages sont vectorisés une fois, sauvegardés en JSON, puis relus pour comparer une query à un index local.

## Hors périmètre

- Qdrant
- index ANN
- mise à jour incrémentale
- suppression partielle
- batch OpenVINO réel optimisé
- Scheduler
