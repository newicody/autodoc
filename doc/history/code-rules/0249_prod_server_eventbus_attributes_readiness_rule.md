# Code rule 0249 - EventBus advanced attribute readiness

Patch 0249 may validate the EventBus attribute allowlist and redaction surface
only.

Required:

```text
EventBus remains observation only
schema_version is required
trace_id/component/phase are required
sql_ref/qdrant_ref/github_ref/project_push_frame_ref are refs only
secret is redacted
large payloads are forbidden as EventBus attributes
```

Forbidden in this phase:

```text
creating EventBus instances
publishing EventBus events
triggering Scheduler
starting threads
writing PostgreSQL
running OpenVINO inference
creating/upserting Qdrant collections or points
calling GitHub API
adding non-stdlib dependencies
```
