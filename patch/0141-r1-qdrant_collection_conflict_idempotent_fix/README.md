# 0141-r1 — Qdrant collection conflict idempotent fix

Fixes the live Qdrant smoke path when the smoke collection already exists.

Qdrant returns HTTP 409 when `PUT /collections/<name>` is called for an existing collection.  For the operator smoke this means the collection is already ensured, so the tool now treats 409 as an idempotent collection-already-exists result and continues with upsert/search.

No new Qdrant adapter, qdrant_client dependency, Scheduler integration, RouteProxy worker, daemon, or context-contract mutation is introduced.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py tests/rules/test_qdrant_projection_operator_rest_smoke_0140_rule.py
```
