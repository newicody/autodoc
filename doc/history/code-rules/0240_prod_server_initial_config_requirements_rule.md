# Code rule 0240 - production server initial configuration requirements

Patch 0240 may define initial production server configuration requirements only.

Required direction:

```text
OpenRC -> launcher -> Scheduler -> handlers/components
EventBus -> PassiveSupervisorSink -> CellularState
SQL -> Qdrant projection -> recall -> SQL rehydrate
GitHub artifacts -> server import -> Scheduler authority
```

Required boundaries:

```text
Scheduler is orchestration authority
EventBus is observation path
PassiveSupervisor is downstream only
PostgreSQL is durable authority
Qdrant is projection/recall only
GitHub is artifact exchange unless publication review enables a remote update
Copilot preliminary output is advisory only
```

Forbidden in this phase:

```text
starting OpenRC
creating Scheduler/EventBus instances
starting threads in __init__
publishing EventBus events
calling GitHub API
publishing to GitHub
executing PostgreSQL DDL/DML
creating/upserting Qdrant collections or points
adding non-stdlib dependencies
```
