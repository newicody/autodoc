# 0139 — Qdrant projection live smoke existing path

Purpose: prepare the first Qdrant projection live-smoke through existing repo surfaces only.

Scope:

- Reuses `src/inference/qdrant_projection_adapter.py` as the existing projection membrane.
- Reuses `src/context/vector_collection_registry.py`.
- Reuses `src/context/vector_indexing_job_plan.py`.
- Adds an operator smoke planner with dry-run default.
- `--execute` delegates only if the existing adapter already exposes a known smoke entrypoint.
- Does not create a new Qdrant adapter, worker daemon, Scheduler runner, or RouteProxy worker.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_qdrant_projection_live_smoke_existing_path_0139.py tests/rules/test_qdrant_projection_live_smoke_existing_path_0139_rule.py
```

Operator command:

```bash
python tools/run_qdrant_projection_live_smoke.py . --format markdown
```

Optional backend attempt:

```bash
python tools/run_qdrant_projection_live_smoke.py . \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --execute
```
