# Test report — Phase 5.15 — SourceCandidate local storage/report

## Vérifications locales effectuées dans l'environnement de génération

```text
py_compile src/context/source_candidate_store.py: OK
py_compile src/context/__init__.py: OK
pytest source_candidate_store isolé: 8 passed
DOT 00_global.dot: OK
DOT 38_source_candidate_contract.dot: OK
DOT 39_source_candidate_storage_report.dot: OK
```

Le pytest isolé a été exécuté avec `source_candidate.py` + `source_candidate_store.py`
dans un package temporaire minimal pour valider la logique pure du store. Les
tests complets doivent être exécutés dans le dépôt utilisateur après extraction.

## Tests recommandés

```bash
PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context/test_local_context_loop_cli.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.15 ajoute une bordure IO locale explicite avec JSON atomique ; aucune règle de programmation nouvelle n'est nécessaire.
```
