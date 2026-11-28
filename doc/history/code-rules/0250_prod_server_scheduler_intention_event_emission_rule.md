# Code rule 0250 - Scheduler intention event emission

Patch 0250 may derive immutable EventBus-shaped envelopes from typed Scheduler
intentions only.

Required:

```text
Scheduler intention remains command-side input
Event envelope is observation-side data
EventBus remains observation only
schema_version/event_type/trace_id/component/phase are present
secret fields are redacted
large payloads are not included
```

Forbidden in this phase:

```text
creating EventBus instances
publishing EventBus events
calling Scheduler.run
triggering handlers
starting threads
writing PostgreSQL
running OpenVINO inference
creating/upserting Qdrant collections or points
calling GitHub API
adding non-stdlib dependencies
```
