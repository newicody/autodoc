# 0141 — local vector indexing live smoke

Adds an operator chain smoke tool that composes the existing OpenVINO/E5 and Qdrant smoke surfaces:

- `tools/run_openvino_e5_live_smoke.py`
- `tools/run_qdrant_projection_live_smoke.py`
- existing OpenVINO/Qdrant membranes under `src/inference`

This patch does not add a new adapter, Scheduler runner, RouteProxy worker, or daemon.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_local_vector_indexing_live_smoke_0141.py tests/rules/test_local_vector_indexing_live_smoke_0141_rule.py
```

Operator dry-run:

```bash
python tools/run_local_vector_indexing_live_smoke.py . --format markdown
```

Operator live chain:

```bash
python tools/run_local_vector_indexing_live_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --execute
```
