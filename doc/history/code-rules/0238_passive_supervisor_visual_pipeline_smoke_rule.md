# Code rule 0238 — passive supervisor visual pipeline smoke

The visual pipeline is a local read-only composition of existing tools.

Required chain:

```text
0234 -> 0236 -> 0237
```

Required runtime boundary:

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

Forbidden:

```text
runtime authority
renderer dependency
non-stdlib dependency
SQL/Qdrant/GitHub mutation
proxy/SHM/policy control
```
