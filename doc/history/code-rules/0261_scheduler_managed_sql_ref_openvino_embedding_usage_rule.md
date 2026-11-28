# Code rule 0261 - Scheduler-managed sql_ref to OpenVINO embedding usage

Required:

```text
Scheduler-managed sql_ref to OpenVINO embedding usage
sql_ref -> SQL rehydrate -> OpenVINO/E5 passage embedding
Scheduler does not start OpenVINO
Qdrant is not involved in 0261
execute requires policy_decision_id
```

Forbidden:

```text
Qdrant projection
Qdrant recall
new embedding model
new RuntimeManager
Scheduler.run modification
OpenVINO service start
PostgreSQL daemon start
EventBus command path
```

0262 may project the embedding toward Qdrant with `payload.sql_ref`.
