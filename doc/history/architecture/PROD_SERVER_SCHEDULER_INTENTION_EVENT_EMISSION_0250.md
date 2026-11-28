# Scheduler intention event emission - 0250

## Intent

This patch derives an immutable observation envelope from a typed Scheduler
intention.

It is the first bridge from command-side intention data to EventBus-shaped facts,
but it still does not publish anything.

No EventBus is created.

No Scheduler.run call is made.

## Direction

```text
TypedSchedulerIntention -> EventEnvelope
```

The envelope uses the attribute surface validated in 0249:

```text
schema_version
event_type
trace_id
component
phase
intent_id
priority
sql_ref
qdrant_ref
payload_hash
```

Secrets are redacted before they appear in the envelope.

## Boundary

EventBus remains observation only. Scheduler remains the command path. This phase
does not dispatch handlers, start threads, write PostgreSQL, run OpenVINO, write
Qdrant, or call GitHub.

## Next step

0251 can use this envelope shape around a minimal Scheduler-controlled SQL write
handler while still keeping events as observations, not actions.
