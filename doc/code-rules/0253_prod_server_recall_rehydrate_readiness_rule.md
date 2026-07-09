# Code rule 0253 - recall rehydrate readiness

The recall rehydrate readiness layer is a shape check only.

Required flow:

```text
Qdrant recall payload -> sql_ref -> PostgreSQL rehydrate read
```

Required authority:

```text
PostgreSQL remains the durable authority
Qdrant remains projection and recall only
```

Forbidden in this phase:

```text
Qdrant search
Qdrant upsert
SQL SELECT execution
PostgreSQL write
OpenVINO inference
EventBus publication
Scheduler.run
GitHub API calls
non-stdlib dependency
```
