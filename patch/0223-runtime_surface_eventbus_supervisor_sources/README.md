# 0223 - Runtime Surface EventBus Supervisor Sources

Direct update to the existing passive bus supervisor surface.

This patch adds canonical EventBus supervision helpers for RouteProxy,
ControlProxy, SHM ring/status, and policy gate visibility. It extends
`PassiveSupervisorSink` with downstream-only accept helpers and adds a smoke tool
that verifies runtime surface events can feed the in-memory cellular state and
optional snapshot/audit outputs.

Boundary:

- Scheduler remains upstream orchestration authority.
- EventBus remains the canonical transport.
- PassiveSupervisorSink remains downstream-only.
- No new EventBus implementation.
- No Scheduler import and no `Scheduler.run` call.
- No proxy control.
- No raw SHM read or mmap access.
- No policy decision.
- No SQL/Qdrant write.
- No GitHub mutation.
- No non-stdlib dependency.

Apply after 0220, 0220-r1, 0221, and 0222.
