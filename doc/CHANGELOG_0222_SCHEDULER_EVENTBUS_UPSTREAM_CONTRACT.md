# Changelog — 0222 Scheduler EventBus upstream contract

## Added

- Written architecture contract for Scheduler-origin EventBus observation.
- Rule file locking Scheduler as upstream authority and passive supervisor as downstream-only.
- DOT diagram for the canonical Scheduler -> EventBus -> PassiveSupervisorSink flow.
- Rule tests covering the authority boundary and forbidden runtime shortcuts.

## Not changed

- No runtime code.
- No Scheduler implementation.
- No EventBus implementation.
- No `Scheduler.run()` call or modification.
- No proxy, SHM, policy, SQL, Qdrant, GitHub, or VisPy integration.
