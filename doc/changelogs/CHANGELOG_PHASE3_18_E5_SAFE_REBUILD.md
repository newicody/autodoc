# Changelog Phase 3.18 — E5 safe rebuild

## Ajouté

- `src/inference/e5_rebuild_cli.py`
  - `E5CorpusRebuildValidation`
  - `E5CorpusRebuildCliOutput`
  - `build_rebuild_parser()`
  - `run_rebuild_async()` / `run_rebuild()`
  - `rebuild_staging_path()`
- `tools/rebuild_e5_corpus.py`
- `tests/inference/test_e5_rebuild_cli.py`
- `doc/docs/architecture/inference/56_e5_safe_rebuild.dot`

## Modifié

- `src/inference/__init__.py`
- `README.md`
- `doc/ARCHITECTURE_LAYERS.md`
- `doc/docs/architecture/inference/40_inference.dot`
- `doc/docs/architecture/inference/50_e5_corpus.dot`
- `doc/docs/architecture/tests/80_tests.dot`

## Intention

La Phase 3.18 transforme le cycle manuel :

```text
build vers corpus.next.json
validation manuelle
mv corpus.next.json corpus.json
```

en commande contrôlée :

```text
staging -> validation -> promotion finale
```

Le corpus final n'est remplacé que si le candidat a été écrit, relu et validé. Une recherche de validation peut être exécutée avant promotion avec `--validation-query`.

## Hors périmètre

- Pas de Qdrant.
- Pas de changement Scheduler.
- Pas de nouveau format de corpus.
- Pas de suppression automatique de stale locks.
