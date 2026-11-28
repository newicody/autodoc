# Code rule 0260 - Scheduler-managed DbApiSqlContextStore binding

Required:

```text
Scheduler-managed DbApiSqlContextStore binding
replaces the 0259 demo store
Scheduler does not start PostgreSQL
does not create a new SQL store
uses existing DbApiSqlContextStore
sql.context.write
```

Forbidden:

```text
new SQL store
SQL worker
SQL orchestrator
RuntimeManager
Scheduler.run modification
PostgreSQL daemon start
Qdrant call
OpenVINO call
GitHub call
EventBus command path
```

0261 can use the resulting sql_ref for OpenVINO projection under Scheduler
ownership.
