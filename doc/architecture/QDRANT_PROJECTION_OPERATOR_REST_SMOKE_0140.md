# 0140 — Qdrant projection operator REST smoke

0140 extends the existing Qdrant smoke operator, not the Scheduler.

The 0139 smoke showed that the repository is ready for a Qdrant projection smoke but the existing adapter had no executable smoke entrypoint.  0140 therefore extends the existing `tools/run_qdrant_projection_live_smoke.py` operator tool to execute a real local REST smoke while still reusing the existing adapter contracts.

## Boundary lock

- the existing src/inference/qdrant_projection_adapter.py contract remains the Qdrant projection membrane
- operator REST execution is allowed only in tools/run_qdrant_projection_live_smoke.py
- do not create VectorQdrantProjectionAdapter
- do not import Qdrant from Scheduler, RouteProxy, PolicyEngine, Dispatcher, or context contracts
- Qdrant stores projection and recall indexes, not durable truth
- SQLContextStore remains durable context authority
- dry-run remains default; `--execute` is required before touching Qdrant

## Live path

```text
tools/run_qdrant_projection_live_smoke.py --execute
-> existing OpenVINOEmbeddingText/OpenVINOEmbeddingVector contracts
-> existing qdrant_projection_adapter build_qdrant_projection_point
-> operator REST PUT collection
-> operator REST upsert point
-> operator REST search vector
-> print sql_ref and point id
```

This is not a new application runtime. It is an operator smoke test proving that the local Qdrant backend can receive and recall one projection.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: 0140 documents that REST execution for live Qdrant smoke is allowed only in the operator tool and must not leak into Scheduler/RouteProxy/context contracts.
live_path_status: smoke
live_path_uses_real_backend: true_when_execute_is_used
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
