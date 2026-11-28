# Code rule 0251 - SQL controlled write handler readiness

Patch 0251 may derive a dry-run SQL controlled write handler frame only.

Required:

```text
Scheduler intention is the command-side input
Event envelope is observation-side data
SQLControlledWriteRequest targets context_records
write operation is insert_if_absent
idempotency key is payload_hash
SQL text is preview-only
```

Forbidden in this phase:

```text
opening PostgreSQL connections
executing SQL
calling Scheduler.run
dispatching handlers
creating EventBus instances
publishing EventBus events
running OpenVINO inference
creating/upserting Qdrant collections or points
calling GitHub API
adding non-stdlib dependencies
```
