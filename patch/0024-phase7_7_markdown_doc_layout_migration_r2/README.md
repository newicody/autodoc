# 0024-r2 — Phase 7.7 Markdown Doc Layout Migration

This r2 patch avoids touching files that already diverged locally:

- no `tools/__init__.py` creation
- no modification hunk for `tests/tools/test_markdown_doc_layout.py`

It adds the migration command that moves Markdown files under `doc/` and rewrites
Python tests that reference moved Markdown paths.

## Apply patch

```bash
python apply_patch_queue.py --patch 0024-phase7_7_markdown_doc_layout_migration_r2 --dry-run
python apply_patch_queue.py --patch 0024-phase7_7_markdown_doc_layout_migration_r2 --commit --push
```

## Then run the migration

```bash
python tools/markdown_doc_migrate_repo.py   --root .   --apply   --report-file doc/maintenance/markdown_doc_migration_report.json
```

## Validate after migration

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_markdown_doc_layout.py
PYTHONPATH=src:. pytest -q tests/tools/test_markdown_doc_migrate_repo.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Commit migration result

```bash
git add -A
git commit -m phase7-7-markdown-doc-layout-migration-apply
git push
```
