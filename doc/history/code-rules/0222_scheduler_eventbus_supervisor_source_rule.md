# 0222 Scheduler EventBus Supervisor Source Rule

Patch 0222 connects Scheduler visibility to the existing passive supervisor by
standardizing the Scheduler EventBus event shape. It must remain a direct update
to the 0220/0221 passive supervisor surface.

Required boundary:

- Scheduler is the upstream orchestration authority.
- Scheduler events may be represented as canonical EventBus events.
- The passive supervisor may accept those events downstream.
- The passive supervisor must not import Scheduler.
- The passive supervisor must not call `Scheduler.run`.
- The passive supervisor must not dispatch scheduler handlers.
- The patch must not introduce a new EventBus implementation.
- The patch must not control RouteProxy or ControlProxy.
- The patch must not read raw SHM or mmap buffers.
- The patch must not decide policy.
- The patch must not write SQL or Qdrant.
- The patch must not mutate GitHub.
- The patch must stay stdlib-only.

`events.jsonl` remains optional audit/replay output. The runtime path remains
Scheduler -> EventBus -> PassiveSupervisorSink -> in-memory cellular state.
