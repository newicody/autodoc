# PHASE3_15_TEST_REPORT — E5 incremental corpus

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py
```

## Résultats

```text
compileall OK
184 passed, 1 skipped in 0.89s
main.py exit code: 0
DOT_OK
DOT links: 3 passed
```

Les warnings Graphviz `Orthogonal edges do not currently handle edge labels` sont connus et non bloquants.

## Portée

- Ajout du build incrémental par hash.
- Ajout de `--reuse-index` à `build_e5_corpus.py`.
- Ajout de métadonnées `source_hash`, `source_bytes`, `chunk_hash`, `document_hash`, `embedding_reused`.
- Aucun changement Scheduler / Dispatcher / ComponentProxy.
- Aucun Qdrant.
- Aucun `.svg` inclus dans l'artefact.
