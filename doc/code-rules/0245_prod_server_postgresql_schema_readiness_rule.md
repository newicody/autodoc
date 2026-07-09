# Code rule 0245 - PostgreSQL schema readiness

Patch 0245 may derive PostgreSQL schema readiness from the production server INI
only.

Required:

```text
validated INI is used
PostgreSQL table sections are checked
SQL text is preview-only
no PostgreSQL connection is opened
no SQL is executed
```

Forbidden in this phase:

```text
opening PostgreSQL connections
executing SQL
starting OpenRC
creating Scheduler/EventBus instances
publishing EventBus events
calling GitHub API
creating/upserting Qdrant collections or points
adding non-stdlib dependencies
```
