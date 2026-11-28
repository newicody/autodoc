# CHANGELOG Phase 3.15 — E5 incremental corpus

## Objectif

Éviter de recalculer les embeddings des passages inchangés lors d'une reconstruction de corpus local E5.

## Ajouts

- `src/inference/e5_incremental.py`
  - `E5IncrementalCorpusBuilder`
  - `E5IncrementalBuildStats`
  - `E5IncrementalBuildResult`
  - `make_e5_document_hash()`
  - `embedding_matches_document()`
  - `reuse_embedding()`
- `tests/inference/test_e5_incremental.py`

## Modifications

- `src/inference/e5_corpus_cli.py`
  - option `--reuse-index`
  - sortie `reused_count`, `embedded_count`, `removed_count` en build incrémental
- `src/inference/e5_sources.py`
  - métadonnées `source_hash`, `source_bytes`, `chunk_hash`
- `src/inference/__init__.py`
  - exports des nouvelles briques incrémentales
- `README.md`
  - documentation d'utilisation de `--reuse-index`
- `doc/ARCHITECTURE_LAYERS.md`
  - état Phase 3.15
- DOT inference
  - ajout du sous-graphe `53_e5_incremental.dot`

## Garantie

Le format JSON du corpus reste `missipy.e5.corpus.v1`. Les nouveaux champs de hash sont ajoutés dans les métadonnées. Les anciens index restent lisibles.
