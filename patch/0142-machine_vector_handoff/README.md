# 0142 — machine vector handoff

Purpose: close the 0141 gap by reusing the existing E5 CLI JSON full-vector output and feeding that machine vector into the existing Qdrant smoke tool.

Scope:

- Extends `tools/run_local_vector_indexing_live_smoke.py`.
- Extends `tools/run_qdrant_projection_live_smoke.py` with `--vector-json`.
- Reuses `tools/embed_e5.py --format json --full-vector`.
- Does not create any new OpenVINO/Qdrant adapter, scheduler runner, RouteProxy worker, or daemon.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_machine_vector_handoff_0142.py tests/rules/test_machine_vector_handoff_0142_rule.py
PYTHONPATH=src:. pytest -q tests/tools/test_local_vector_indexing_live_smoke_0141.py tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py tests/tools/test_machine_vector_handoff_0142.py
```
