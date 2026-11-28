# Part 9.1 VisPy Cell Lens Viewer Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/visualization/test_cell_lens_health.py
PYTHONPATH=src:. pytest -q tests/visualization/test_cell_lens_projection.py
PYTHONPATH=src:. pytest -q tests/tools/test_visualize_cell_population_vispy.py
PYTHONPATH=src:. pytest -q tests/rules/test_vispy_cell_lens_viewer_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
health tests: pass
projection tests: pass
tool boundary tests: pass
rules: pass
full suite: pass
```
