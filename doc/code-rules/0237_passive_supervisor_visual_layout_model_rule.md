# Code rule 0237 — passive supervisor visual layout model

The visual layout model is a read-only downstream projection.

Required path:

```text
EventBus -> PassiveSupervisorSink -> CellularState
snapshot/read-model -> visual layout model
```

Forbidden:

```text
Scheduler execution
EventBus creation
proxy/SHM/policy control
SQL/Qdrant/GitHub mutation
renderer dependency
non-stdlib dependency
```
