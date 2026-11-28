# Part 10.4 Cell Lens Local Demo Bundle Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_cell_lens_local_demo_bundle.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_lens_local_demo_bundle_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
