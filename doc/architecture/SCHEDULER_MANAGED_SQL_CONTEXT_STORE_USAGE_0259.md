# Scheduler-managed SQLContextStore usage - 0259

## Intent

0259 adapts SQL usage under Scheduler ownership.

Scheduler-managed SQLContextStore usage means:

```text
Scheduler bootstrap attachment
  -> sql.context.write
  -> existing SQLContextStore object
```

Scheduler does not start PostgreSQL.  OpenRC and the host operating system own
the PostgreSQL daemon lifecycle.

Scheduler uses an existing SQLContextStore object.  It does not create a new SQL
store, SQL worker, SQL orchestrator, RuntimeManager, or component-specific
production CLI.

## Capability requirement

The 0258 attachment must expose:

```text
sql.context.write resolves to sql_context_store
sql.context.rehydrate resolves to sql_context_store
```

## Controlled execution

Dry-run is valid without a store object.

Execution requires:

```text
execute=True
policy_decision_id
existing SQLContextStore object
```

The required wording is: execute requires policy_decision_id.

## Boundary

No PostgreSQL daemon start.  No Qdrant call.  No OpenVINO call.  No GitHub call.
No EventBus command path.  No Scheduler.run modification.

Smoke tools remain validation helpers only.  There is no CLI per component as
the runtime API.

## Next step

0260 can bind the real DbApiSqlContextStore constructor or existing factory
surface selected by the 0256/0257 reports, then perform a real controlled write
through Scheduler ownership.
