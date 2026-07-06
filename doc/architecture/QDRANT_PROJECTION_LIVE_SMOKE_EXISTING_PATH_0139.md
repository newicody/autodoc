# 0139 — Qdrant projection live smoke through existing path

0139 prepares the first Qdrant projection live smoke through existing surfaces only.

The phase adds an operator smoke planner, not a new adapter.  It inspects the existing Qdrant projection membrane and prepares a deterministic 384-dim smoke projection.  Backend execution remains opt-in.

## Existing surfaces

src/inference/qdrant_projection_adapter.py is the existing Qdrant projection membrane.

src/context/vector_collection_registry.py is the existing collection registry.

src/context/vector_indexing_job_plan.py is the existing projection job contract.

## Boundary

Do not create a parallel VectorQdrantProjectionAdapter.

Qdrant stores projection/recall indexes, not durable truth.

SQLContextStore remains durable context authority.

Scheduler remains outside Qdrant.

RouteProxy remains outside Qdrant.

The smoke tool may inspect the existing adapter by AST.  It does not import qdrant_client itself.  If the existing adapter already exposes a smoke entrypoint, `--execute` delegates to it.  If not, the next patch must extend `src/inference/qdrant_projection_adapter.py` rather than adding a parallel adapter.

## Operator command

```bash
python tools/run_qdrant_projection_live_smoke.py . --format markdown
```

Backend execution is explicit:

```bash
python tools/run_qdrant_projection_live_smoke.py . \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --execute
```

dry-run is the default.

--execute is required for backend execution.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: locks Qdrant live-smoke reuse before adding or modifying any executable adapter entrypoint.
live_path_status: smoke-prep
live_path_uses_real_backend: optional_execute
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
