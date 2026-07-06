# 0119 — QdrantProjectionAdapter

This patch adds the Qdrant projection boundary after OpenVINO embeddings.

It introduces immutable Qdrant target, policy, point, batch, write-result, and recall-hit structures. The adapter consumes `OpenVINOEmbeddingBatch`, builds bounded Qdrant-ready points carrying `sql_context_ref`, and delegates upsert/search to an injected executor.

The adapter does not import qdrant-client, OpenVINO, PostgreSQL drivers, HTTP clients, sockets, or kernel components. SQL remains the authority; Qdrant results are refs that must be re-hydrated from SQL.

## Apply

```bash
python apply_patch_queue.py --patch 0119-qdrant_projection_adapter --dry-run
python apply_patch_queue.py --patch 0119-qdrant_projection_adapter --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_qdrant_projection_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_qdrant_projection_adapter_0119_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
