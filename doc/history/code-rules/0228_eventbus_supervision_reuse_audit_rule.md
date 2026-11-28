# 0228 code rule — EventBus supervision reuse audit

Before implementing any functional passive supervision sink, audit existing EventBus,
Scheduler, and passive supervisor surfaces.

Required rule:

```text
audit existing EventBus and passive supervision surfaces first
reuse or extend existing code when possible
no new bus without documented proof that no suitable bus exists
no bridge parallel to EventBus as the live path
no status.json/events.jsonl as mandatory runtime spine
Scheduler.run must not be called, wrapped, or controlled by the supervisor
PassiveSupervisorSink remains downstream-only
snapshot and audit/replay remain optional outputs
```

The 0228 audit tool is read-only and must not import runtime modules, control proxy,
mutate SHM, decide policy, write SQL/Qdrant, mutate GitHub, or execute Scheduler.run.
