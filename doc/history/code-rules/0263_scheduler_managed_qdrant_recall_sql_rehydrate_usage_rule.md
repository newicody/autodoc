# Code rule 0263 - Scheduler-managed Qdrant recall to SQL rehydrate usage

Required:

```text
Scheduler-managed Qdrant recall to SQL rehydrate usage
Qdrant recall -> sql_ref -> SQL rehydrate
Qdrant is recall only and carries refs
SQL remains the durable authority
execute requires policy_decision_id
```

Forbidden:

```text
SQL content authority in Qdrant
OpenVINO execution
Qdrant daemon start
new RuntimeManager
Scheduler.run modification
PostgreSQL daemon start
EventBus command path
```

0264 may compose the closed ResultFrame.
