# Phase 7.7 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_markdown_doc_migrate_repo.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Optional migration command

```bash
python tools/markdown_doc_migrate_repo.py \
  --root . \
  --apply \
  --report-file doc/maintenance/markdown_doc_migration_report.json
```

## Expected

```text
markdown migration tests: pass
rules: pass after migration
full suite: pass after migration
```
