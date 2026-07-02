# Phase 7.13 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_docs_svg_build_policy.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Optional post-make workflow

```bash
cd doc
make
cd ..

python tools/docs_svg_build_policy.py \
  --root . \
  --clean \
  --check \
  --report-file doc/maintenance/docs_svg_build_policy_report.json
```

## Expected

```text
docs SVG policy tests: pass
rules: pass after cleanup
full suite: pass
```
