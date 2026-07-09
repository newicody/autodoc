# EventBus advanced attribute readiness - 0249

## Intent

This patch validates the advanced EventBus attribute surface for the production
server.

EventBus remains observation only. Scheduler remains the command path.

## Attribute surface

Required attributes:

```text
schema_version
event_type
trace_id
component
phase
```

Reference attributes:

```text
intent_id
result_id
sql_ref
qdrant_ref
github_ref
project_push_frame_ref
payload_hash
priority
```

Redacted attributes:

```text
secret
```

## Payload policy

The EventBus policy is refs only, no large payloads. Large data stays in SQL,
reports, or future data-plane refs. EventBus events may carry `sql_ref`,
`qdrant_ref`, `github_ref`, `project_push_frame_ref`, and `payload_hash`.

## Projection relation

0249 composes the projection path readiness from 0248 so future projection events
can expose the SQL/OpenVINO/Qdrant references without embedding the vector or the
source payload into the EventBus.

## Boundary

0249 validates attributes only. It does not create EventBus, publish events,
trigger Scheduler, start threads, write PostgreSQL, run OpenVINO inference, write
Qdrant, or call GitHub.

## Next step

0250 can use this attribute surface for real Scheduler-intention event emission
while preserving the observation-only EventBus boundary.
