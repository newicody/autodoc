# Scheduler-managed DbApiSqlContextStore record adapter - 0260 r8

0260-r8 adds the missing record adapter module required by the r6 binding
change.

The wrapper adapts real stores that expose `upsert_record(record)` and expect a
record-like object with `context_ref`.

Boundary:

```text
Scheduler does not start PostgreSQL
does not create a new SQL store
uses existing DbApiSqlContextStore
does not modify Scheduler.run
```
