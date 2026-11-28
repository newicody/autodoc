# Changelog — 0183 Route handler surface resolver

## Added

- Read-only resolver for route handler surfaces.
- Detection of request adapter, command handler, readback handler, command
  builder, ControlProxy wrapper, and scheduler handshake surfaces.
- Signature extraction for discovered functions through AST.
- Tests/rules locking that no handler import, handler call, Scheduler
  modification, EventBus instantiation, frame write, GitHub API, network,
  conversion, inference, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No route handler execution.
- No ControlProxy/RouteProxy frame write.
