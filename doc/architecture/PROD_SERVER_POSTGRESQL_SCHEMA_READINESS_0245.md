# PostgreSQL schema readiness - 0245

## Intent

This patch checks PostgreSQL schema readiness from the production server INI.

It reads the PostgreSQL table sections and derives:

```text
table names
primary keys
column names
JSONB columns
required indexes
idempotent SQL text for review
```

No PostgreSQL connection is opened.

## SQL preview

SQL text is preview-only in this phase. It is generated so the expected table and
index shape is visible and testable before any server mutation is allowed.

The generated statements use:

```text
CREATE TABLE IF NOT EXISTS
CREATE INDEX IF NOT EXISTS
```

but they are not executed by 0245.

## Boundary

0245 is readiness-only. It does not connect to PostgreSQL, execute SQL, write
PostgreSQL, start OpenRC, create Scheduler/EventBus, publish EventBus events,
call GitHub, or write Qdrant.

## Next step

0246 is reserved for OpenVINO embedding readiness. PostgreSQL apply/check against
a live server can come after the readiness path is explicit and reviewed.
