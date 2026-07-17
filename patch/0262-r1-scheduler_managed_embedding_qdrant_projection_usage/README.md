# 0262-r1-scheduler_managed_embedding_qdrant_projection_usage

Adds the 0262 projection step:

```text
0261 embedding report -> OpenVINOEmbeddingBatch -> QdrantProjectionBatch
```

SQL remains the durable authority and the resulting point payload carries a
`sql_ref` alias in addition to the existing adapter's `sql_context_ref`.

Apply:

```bash
python apply_patch_queue.py --patch 0262-r1-scheduler_managed_embedding_qdrant_projection_usage --commit --push --allow-dirty
```
