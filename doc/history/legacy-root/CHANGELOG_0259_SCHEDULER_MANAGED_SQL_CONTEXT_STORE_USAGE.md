# Changelog 0259 - Scheduler-managed SQLContextStore usage

## r1

Adds the Scheduler-managed SQLContextStore usage boundary.

The patch validates that the 0258 bootstrap attachment exposes
`sql.context.write` and `sql.context.rehydrate` through `sql_context_store`.
It supports controlled execution only when a policy decision id and existing
store object are supplied.

It does not create a new SQL store, does not start PostgreSQL, does not modify
Scheduler.run, and does not create a RuntimeManager.
