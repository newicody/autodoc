# SQL controlled write handler readiness - 0251

## Intent

This patch derives a minimal SQL controlled write handler frame from the typed
Scheduler intention event surface introduced in 0250.

No SQL is executed.

## Handler frame

The dry-run handler frame links:

```text
TypedSchedulerIntention
  -> EventEnvelope
  -> SQLControlledWriteRequest
```

The request targets:

```text
handler = handler.sql_context_store.controlled_write
table = context_records
operation = insert_if_absent
primary_key = id
idempotency_key = payload_hash
```

The SQL text is preview-only and uses `ON CONFLICT (id) DO NOTHING` to describe
the intended idempotent behavior.

## Boundary

Scheduler remains command authority. EventBus remains observation only. This
phase does not call Scheduler.run, dispatch handlers, create EventBus, publish
events, connect to PostgreSQL, execute SQL, run OpenVINO, write Qdrant, or call
GitHub.

## Next step

0252 can derive the embedding/projection readiness from this handler frame so the
future controlled write result can feed OpenVINO and Qdrant without bypassing
SQL authority.
