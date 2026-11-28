# Changelog — 0223 Runtime Surface EventBus upstream contract

## Added

- Written architecture contract for RouteProxy, ControlProxy, SHM, and Policy observation through EventBus.
- Rule file locking runtime surfaces as upstream emitters and passive supervision as downstream-only.
- DOT diagram for runtime surface event emission into the passive supervisor.
- Rule tests covering the authority boundary and forbidden shortcuts.

## Not changed

- No runtime code.
- No new EventBus implementation.
- No proxy controller.
- No `/dev/shm` or mmap reader.
- No policy engine.
- No `Scheduler.run()` call or modification.
- No SQL, Qdrant, GitHub, or VisPy integration.
