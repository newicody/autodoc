# Code rule 0259 - Scheduler-managed SQLContextStore usage

Required:

```text
Scheduler-managed SQLContextStore usage
Scheduler does not start PostgreSQL
Scheduler uses an existing SQLContextStore object
sql.context.write resolves to sql_context_store
execute requires policy_decision_id
no CLI per component
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

0260 can bind the real DbApiSqlContextStore constructor selected by the reuse
reports.  0259 only adapts the Scheduler-managed usage boundary and controlled
execution gate.
