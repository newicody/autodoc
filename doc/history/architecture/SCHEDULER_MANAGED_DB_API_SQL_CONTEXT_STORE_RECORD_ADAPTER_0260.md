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

## r9

The real `DbApiSqlContextStore` validates `context_ref` as a typed SQL
reference.  The adapter now normalises generated context references so they
start with `sql:` while preserving already-typed `sql:` references.

## r10

The real execution path reached SQLite and failed when the target database had
no `sql_context_records` table.  The adapter now calls an existing schema
bootstrap hook when the bound store exposes one.  This does not invent a schema;
it delegates schema readiness to the existing DbApiSqlContextStore surface.

## r11

The adapter now reuses the existing `build_sql_context_record` helper exposed by
`context.sql_context_store`.  It no longer uses a generic SimpleNamespace as the
primary record path.  Scheduler text kinds such as `passage` and `query` are
mapped to the existing SQL kind `inference_context`.
