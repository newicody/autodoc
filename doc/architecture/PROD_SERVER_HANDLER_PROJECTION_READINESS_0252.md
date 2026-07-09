# Handler projection readiness - 0252

## Intent

This patch derives the future projection request from the SQL controlled write
handler frame prepared in 0251.

```text
SQL handler frame -> OpenVINO embedding -> Qdrant projection
```

No embedding is computed.

No Qdrant point is written.

## Projection request

The readiness output carries:

```text
source_table = context_records
text_source_field = payload_json
sql_ref = context_records.id
content_hash = sha256:sample-content-hash
openvino_model_id = openvino.embedding.e5-small
vector_dimension = 384
qdrant_collection = autodoc_context_e5_small
qdrant_distance = cosine
payload.sql_ref = context_records.id
payload.model_id = openvino.embedding.e5-small
payload.embedding_version = 0252.r1
payload.content_hash = sha256:sample-content-hash
```

SQL remains the durable authority. Qdrant remains a projection/recall surface.

## Boundary

0252 is readiness-only. It does not execute SQL, run OpenVINO inference, call
Qdrant, write points, publish EventBus events, dispatch handlers, call
Scheduler.run, or call GitHub.

## Next step

0253 can define recall readiness from Qdrant payload `sql_ref` back to SQL
rehydration.
