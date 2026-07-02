# Markdown doc migration

Phase 7.7 applies the Markdown documentation layout and updates Python tests
that reference moved Markdown files.

The migration keeps:

```text
README.md
patch/**/README.md
```

and moves reports/manifests/changelogs/code-rule docs under `doc/`.

## Dry-run

```bash
python tools/markdown_doc_migrate_repo.py \
  --root . \
  --report-file doc/maintenance/markdown_doc_migration_report.json
```

## Apply

```bash
python tools/markdown_doc_migrate_repo.py \
  --root . \
  --apply \
  --report-file doc/maintenance/markdown_doc_migration_report.json
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_markdown_doc_layout.py
PYTHONPATH=src:. pytest -q tests/tools/test_markdown_doc_migrate_repo.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

The migration must be committed with `git add -A` so moved Markdown files and
rewritten tests are recorded together.
