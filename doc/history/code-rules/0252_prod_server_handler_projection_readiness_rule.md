# Code rule 0252 - handler projection readiness

Patch 0252 may derive projection readiness from the SQL handler frame only.

Required:

```text
SQL handler frame feeds projection request
OpenVINO shape is reused
Qdrant collection shape is reused
payload keeps sql_ref/model_id/embedding_version/content_hash
SQL remains durable authority
Qdrant remains projection/recall only
```

Forbidden in this phase:

```text
executing SQL
running OpenVINO inference
calling Qdrant API
writing Qdrant points
dispatching handlers
calling Scheduler.run
publishing EventBus events
calling GitHub API
adding non-stdlib dependencies
```
