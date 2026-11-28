# Changelog 0260 - Scheduler-managed DbApiSqlContextStore binding

## r1

Adds discovery and binding for the existing DbApiSqlContextStore surface.

The patch replaces the 0259 demo store path with an existing-store binding while
preserving Scheduler ownership, the `sql.context.write` capability, and the
external PostgreSQL lifecycle boundary.

## r2

Fixes the candidate discovery/import path: strict class matching prevents the binder from selecting its own helper classes, and file-path loading avoids `context` package cache collisions during temporary-root tests.
