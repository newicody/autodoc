# Changelog — 0181 Route handler surface audit

## Added

- Read-only route handler surface audit CLI.
- AST/text inspection of existing handler-related files.
- Report with file presence, SHA256, AST parse status, expected symbols, and
  detected imports.
- Tests/rules locking that no handler import, handler call, Scheduler
  modification, EventBus instantiation, frame write, GitHub API, network,
  conversion, inference, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No route handler execution.
- No ControlProxy/RouteProxy frame write.
