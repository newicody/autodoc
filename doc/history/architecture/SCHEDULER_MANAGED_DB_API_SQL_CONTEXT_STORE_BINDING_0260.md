# Scheduler-managed DbApiSqlContextStore binding - 0260

## Intent

0260 replaces the 0259 demo store with an existing DbApiSqlContextStore binding.

The goal is not to invent a new SQL store.  The goal is to discover and bind the
existing durable SQL context surface selected by the 0256/0257 reports, then
route it through the 0259 Scheduler-managed usage path.

## r2 correction

0260-r2 fixes candidate selection: it matches only exact `class DbApiSqlContextStore:` or `class DbApiSqlContextStore(...)` definitions, excludes `DbApiSqlContextStoreBinding*` helper classes, and loads class-definition candidates by file path to avoid Python package-cache collisions.

## Boundary

Scheduler does not start PostgreSQL.  OpenRC and host administration own the
PostgreSQL daemon lifecycle.

0260 does not create a new SQL store, SQL worker, SQL orchestrator,
RuntimeManager, or component-specific production CLI.

The required wording is: uses existing DbApiSqlContextStore.

## Execution gate

Execution requires:

```text
--execute
--policy-decision-id
existing DbApiSqlContextStore constructor compatible with DB-API binding
```

The Scheduler-owned capability remains:

```text
sql.context.write
```

## Next step

0261 can project the resulting sql_ref toward OpenVINO, still under Scheduler
ownership and without hiding OpenVINO behind Qdrant.
