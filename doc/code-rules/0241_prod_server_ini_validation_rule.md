# Code rule 0241 - production server INI validation

Patch 0241 may validate the initial production server INI only.

Required:

```text
ConfigObj-compatible INI layout
stdlib parser in this phase
GitHub token_env = GITHUB_TOKEN
GitHub publication disabled by default
GitHub publication review required
Qdrant payload includes sql_ref
EventBus required attributes include schema_version/event_type/trace_id/component/phase
```

Forbidden in this phase:

```text
non-stdlib dependency
starting OpenRC
creating Scheduler/EventBus instances
publishing EventBus events
calling GitHub API
publishing to GitHub
executing PostgreSQL DDL/DML
creating/upserting Qdrant collections or points
```
