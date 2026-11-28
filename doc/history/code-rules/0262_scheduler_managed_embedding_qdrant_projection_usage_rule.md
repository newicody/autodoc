# Code rule 0262 - Scheduler-managed embedding to Qdrant projection usage

Required:

```text
Scheduler-managed embedding to Qdrant projection usage
embedding -> Qdrant projection with payload.sql_ref
Scheduler does not start Qdrant
SQL remains the durable authority
execute requires policy_decision_id
```

Forbidden:

```text
SQL content authority in Qdrant
OpenVINO execution
new RuntimeManager
Scheduler.run modification
Qdrant daemon start
PostgreSQL daemon start
EventBus command path
```

0263 may recall from Qdrant and rehydrate from SQL.
