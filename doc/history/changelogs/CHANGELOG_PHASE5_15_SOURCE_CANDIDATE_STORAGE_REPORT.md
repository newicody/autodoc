# Changelog — Phase 5.15 — SourceCandidate local storage/report

## Ajouté

- `src/context/source_candidate_store.py`
  - `SourceCandidateStorePolicy`
  - `SourceCandidateReportPolicy`
  - `SourceCandidateStoreSnapshot`
  - `SourceCandidateStoreWriteResult`
  - `SourceCandidateStoreReport`
  - `load_source_candidate_store()`
  - `write_source_candidate_store()`
  - `upsert_source_candidate()`
  - `write_source_candidate_store_report()`
  - `source_candidate_store_snapshot_from_json_dict()`
- `tests/context/test_source_candidate_store.py`
- `doc/SOURCE_CANDIDATE_STORAGE_REPORT.md`
- `doc/docs/architecture/context/39_source_candidate_storage_report.dot`

## Modifié

- `src/context/__init__.py` exporte les contrats de store SourceCandidate.
- `doc/docs/architecture/context/38_source_candidate_contract.dot` pointe vers la Phase 5.15.
- `doc/docs/architecture/00_global.dot` expose la Phase 5.15.

## Frontières

- Aucun stockage base de données.
- Aucun serveur.
- Aucun daemon.
- Aucun réseau.
- Aucune API GitHub.
- Aucun token.
- Aucun Qdrant.
- Aucun LLM.
- Aucun appel OpenVINO.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.15 ajoute une bordure IO locale explicite avec JSON atomique ; aucune règle de programmation nouvelle n'est nécessaire.
```
