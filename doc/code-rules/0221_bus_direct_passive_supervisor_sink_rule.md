# 0221 Bus-Direct Passive Supervisor Sink Rule

Patch 0221 is a direct update to the passive bus supervisor introduced in 0220.
It must not introduce a new bus, a parallel observation engine, or a proxy/policy
controller.

Required boundary:

- Scheduler is the upstream orchestration authority.
- Scheduler may emit or expose canonical EventBus events.
- The passive supervisor is downstream-only and may accept those EventBus events.
- The supervisor must not call `Scheduler.run`.
- The supervisor must not dispatch scheduler handlers.
- The supervisor must not control RouteProxy or ControlProxy.
- The supervisor must not read raw SHM or mmap buffers.
- The supervisor must not decide policy.
- The supervisor must not write SQL or Qdrant.
- The supervisor must not mutate GitHub.
- The supervisor must stay stdlib-only.

`events.jsonl` is optional audit/replay/debug output only. It must not be the
mandatory runtime path. The canonical path is EventBus -> PassiveSupervisorSink
-> in-memory cellular state -> optional snapshot.

VisPy remains a future view adapter only. It may consume snapshots later, but it
must not own the state or become an authority.
