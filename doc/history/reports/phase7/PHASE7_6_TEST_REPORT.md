# Phase 7.6 Test Report

## Commands

```bash
PYTHONPATH=src python -m compileall -q src tests tools
PYTHONPATH=src pytest -q tests/tools/test_markdown_doc_layout.py
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Expected

```text
markdown layout tool tests: pass
rules: pass
full suite: pass
```

## Optional local dry-run

```bash
python tools/markdown_doc_layout.py --root . --report-file doc/maintenance/markdown_layout_plan.json
```
