# Changelog 0245 - PostgreSQL schema readiness

## r1

Added PostgreSQL schema readiness derived from the production server INI.

The patch checks table sections, primary keys, JSONB columns, required indexes,
and emits idempotent SQL text for review without opening a PostgreSQL connection
or executing SQL.
