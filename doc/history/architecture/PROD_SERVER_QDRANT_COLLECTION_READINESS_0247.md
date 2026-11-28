# Qdrant collection readiness - 0247

## Intent

This patch validates that the production server Qdrant collection is aligned with OpenVINO embedding readiness from 0246.

OpenVINO produces vectors. Qdrant stores the vector projection for recall.
SQL remains the durable authority.

```text
SQL durable text
  -> OpenVINO embedding readiness
  -> Qdrant collection readiness
  -> future projection
```

No Qdrant API call is made.

## Required alignment

The Qdrant collection must match the OpenVINO embedding shape:

```text
collection = autodoc_context_e5_small
vector_dimension = 384
distance = cosine
normalized_vectors = true
required_payload includes sql_ref
required_payload includes model_id
required_payload includes embedding_version
required_payload includes content_hash
```

`sql_ref` is mandatory because Qdrant recall must rehydrate durable context
through SQL.

## Boundary

0247 is readiness-only. It does not call Qdrant, create collections, upsert
points, run OpenVINO inference, write PostgreSQL, publish EventBus events, or
call GitHub.

## Next step

0248 can describe the projection path:

```text
SQL record -> OpenVINO embedding -> Qdrant point payload(sql_ref)
```
