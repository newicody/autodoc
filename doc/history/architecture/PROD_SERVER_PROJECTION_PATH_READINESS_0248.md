# Projection path readiness - 0248

## Intent

This patch validates the production projection path as data only:

```text
SQL record -> OpenVINO embedding -> Qdrant point
```

No projection is executed.

## Derived point shape

The future Qdrant point shape is derived from the previous readiness steps:

```text
source_table = context_records
sql_ref_field = id
text_source_field = payload_json
vector_dimension = 384
collection = autodoc_context_e5_small
payload.sql_ref = context_records.id
payload.model_id = openvino.embedding.e5-small
payload.embedding_version = 0248.r1
payload.content_hash = context_records.content_hash
```

The point payload keeps `sql_ref` mandatory so Qdrant recall can rehydrate from
SQL, which remains the durable authority.

## Boundary

0248 composes readiness only. It does not connect to PostgreSQL, run OpenVINO
inference, call Qdrant, create collections, write points, publish EventBus
events, or call GitHub.

## Next step

0249 can attach EventBus advanced attributes to these readiness and future
projection surfaces without changing the command path.
