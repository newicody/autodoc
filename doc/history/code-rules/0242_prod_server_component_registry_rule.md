# Code rule 0242 - production server component registry

Patch 0242 may build a declarative component registry from the validated server
INI only.

Required:

```text
factory references use module:function
component dependency order is computed as data
command path and observation path are explicit
INI validation runs before registry acceptance
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
