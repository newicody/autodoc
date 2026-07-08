# Code rule — 0227 functional resumption supervision gate contract

Before resuming runtime implementation of passive supervision, every patch must pass the functional resumption gate.

Required:

```text
reuse existing EventBus and passive-supervisor surfaces when possible
keep Scheduler as upstream orchestration authority
keep EventBus as the canonical live transport
keep PassiveSupervisorSink downstream-only
keep CellularState as an in-memory projection
keep snapshot/audit/replay optional
update changelog, manifest, rules, and tests
```

Forbidden unless a prior audit documents why no existing surface can be reused:

```text
new EventBus
parallel bridge subsystem
new scheduler wrapper
mandatory events.jsonl live path
status JSON as primary live input
snapshot.json as runtime state owner
```

Always forbidden for passive supervision:

```text
Scheduler.run()
proxy control
SHM mutation
required raw /dev/shm read path
policy decision or override
SQL/Qdrant/GitHub mutation
VisPy in the critical runtime path
```
