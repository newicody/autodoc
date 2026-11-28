# Recall rehydrate readiness - 0253

## Intent

This patch defines recall rehydrate readiness for the production server.

Qdrant recall payload -> sql_ref -> PostgreSQL rehydrate read

The goal is to verify that a future Qdrant recall hit can carry enough payload
metadata to return to PostgreSQL for durable context rehydration.

No Qdrant search is executed.

No SQL SELECT is executed.

## Authority boundary

PostgreSQL remains the durable authority. Qdrant remains a projection and recall
surface only. The recall payload must carry `sql_ref`, `model_id`,
`embedding_version`, and `content_hash`.

The readiness step derives a preview read shape:

```text
SELECT id, kind, payload_json, content_hash, created_at FROM context_records WHERE id = :sql_ref LIMIT 1;
```

## Runtime position

```text
Scheduler-controlled handler -> SQL durable write -> OpenVINO embedding -> Qdrant projection -> Qdrant recall payload -> sql_ref -> PostgreSQL rehydrate read
```

This patch does not create a new deployment system, service manager, Scheduler,
EventBus, handler dispatcher, Qdrant client, or PostgreSQL client.

## Next phase

0254 can define a read-only result frame that joins the recalled Qdrant metadata
with the PostgreSQL rehydrated context shape.
