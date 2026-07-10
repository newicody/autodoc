# Scheduler-managed embedding to Qdrant projection usage - 0262

## Intent

0262 composes the next production prototype step:

```text
embedding -> Qdrant projection with payload.sql_ref
```

The embedding comes from the real 0261 OpenVINO/E5 report. SQL remains the
durable authority; Qdrant receives only projection points carrying the SQL
authority reference.

The required wording is: SQL remains the durable authority.

## Boundary

Scheduler does not start Qdrant. Qdrant remains an external service used by an
Autodoc projection object.

OpenVINO is not executed in 0262. The input embedding report must already exist.

No RuntimeManager is introduced. Scheduler.run is not modified.

## Existing surfaces reused

```text
OpenVINOEmbeddingVector
OpenVINOEmbeddingBatch
build_qdrant_projection_batch
QdrantProjectionTarget
QdrantProjectionPolicy
QdrantProjectionExecutor injection membrane
```

Dry-run validates the embedding mapping and builds a Qdrant-ready batch. Execute
requires a `policy_decision_id` and an injected executor. The smoke executor is a
demo executor only; it is not a Qdrant client.

## Next step

0263 can recall from Qdrant and rehydrate from SQL.
