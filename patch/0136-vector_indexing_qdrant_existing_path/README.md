# 0136 — Vector indexing through existing Qdrant path

Purpose: prove that vector projection should reuse the existing Qdrant projection membrane and collection registry before any production bridge is added.

Scope:

- no new Qdrant adapter
- no Scheduler import of Qdrant
- no RouteProxy import of Qdrant
- no production runtime change
- Qdrant remains projection/recall only
- SQLContextStore remains durable authority

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/inference/test_vector_indexing_qdrant_existing_path_0136.py tests/rules/test_vector_indexing_qdrant_existing_path_0136_rule.py
PYTHONPATH=src:. pytest -q tests/inference tests/rules
```
