# Code rule 0243 - Scheduler/EventBus bootstrap readiness

Patch 0243 may verify Scheduler/EventBus bootstrap readiness only.

Required:

```text
validated INI is used
0242 registry is used
Scheduler is command path
EventBus is observation path
factory references remain data only
```

Forbidden in this phase:

```text
importing factory modules
calling factories
creating Scheduler/EventBus instances
starting OpenRC
starting threads
publishing EventBus events
calling GitHub API
executing PostgreSQL DDL/DML
creating/upserting Qdrant collections or points
adding non-stdlib dependencies
```
