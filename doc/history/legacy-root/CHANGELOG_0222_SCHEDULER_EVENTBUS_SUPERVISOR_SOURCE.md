# Changelog 0222 - Scheduler EventBus Supervisor Source

## Added

- Extended the existing passive supervisor module with `scheduler_supervision_event`.
- Added `PassiveSupervisorSink.accept_scheduler_event` as a downstream-only helper
  for canonical Scheduler EventBus events.
- Added `tools/run_scheduler_eventbus_supervisor_smoke_0222.py` to validate a
  Scheduler upstream event through the passive sink without importing Scheduler
  or calling `Scheduler.run`.
- Added tests for Scheduler event refs, handler payloads, optional audit output,
  and snapshot generation.

## Boundary

- Scheduler remains the upstream orchestration authority.
- EventBus remains the canonical transport.
- The passive supervisor remains downstream-only.
- No Scheduler import.
- No `Scheduler.run` call.
- No scheduler handler dispatch.
- No new EventBus implementation.
- No proxy control, raw SHM read, policy decision, SQL/Qdrant write, GitHub
  mutation, or VisPy dependency.
- No non-stdlib dependency.
