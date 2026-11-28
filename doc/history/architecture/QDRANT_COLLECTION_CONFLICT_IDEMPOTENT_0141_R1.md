# 0141-r1 — Qdrant collection conflict is idempotent

0141-r1 fixes the live smoke path after the first successful Qdrant run.

When `tools/run_qdrant_projection_live_smoke.py --execute` ensures the smoke collection, Qdrant may return HTTP 409 because the collection already exists.  For this operator smoke, that is not a failure; it means the collection is already available and the smoke should continue with upsert and search.

Boundary:

- extends the existing tools/run_qdrant_projection_live_smoke.py operator
- keeps src/inference/qdrant_projection_adapter.py as the existing Qdrant projection membrane
- does not create VectorQdrantProjectionAdapter
- does not import Qdrant from Scheduler, RouteProxy, PolicyEngine, Dispatcher, or context contracts
- Qdrant remains projection and recall only
- SQLContextStore remains durable context authority

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: smoke
live_path_uses_real_backend: true
context_contract_changed: false
search_commands_bounded: n/a
```
