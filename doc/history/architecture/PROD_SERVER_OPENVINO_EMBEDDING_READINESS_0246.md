# OpenVINO embedding readiness - 0246

## Intent

This patch restores OpenVINO as an explicit production-server readiness step.

OpenVINO is the local embedding producer. Qdrant is only the projection/recall
index that consumes those vectors.

```text
SQL durable text
  -> OpenVINO multilingual-e5-small embedding
  -> Qdrant projection
  -> Qdrant recall
  -> SQL rehydrate
```

No model is loaded in this phase.

## Locked embedding shape

The initial readiness surface uses:

```text
model_id = openvino.embedding.e5-small
model = multilingual-e5-small
dimension = 384
normalized = true
pooling = mean
qdrant_distance = cosine
query_prefix = query:
passage_prefix = passage:
```

`query:` is for search/input queries. `passage:` is for indexed corpus passages.

## Boundary

0246 is readiness-only. It does not import OpenVINO, import Transformers, read
model files, load the model, run inference, write PostgreSQL, write Qdrant,
publish EventBus events, or call GitHub.

## Next step

Qdrant comes after OpenVINO. 0247 should validate that the Qdrant collection is
aligned with this embedding shape: dimension 384, cosine distance, normalized
vectors, and `sql_ref` payload for SQL rehydration.
