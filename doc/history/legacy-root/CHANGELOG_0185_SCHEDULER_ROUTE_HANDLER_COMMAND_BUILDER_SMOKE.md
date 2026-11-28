# Changelog — 0185 Scheduler route handler command-builder smoke

## Added

- Controlled command-builder smoke using existing `build_single_frame_route_command`.
- Optional `scheduler_route_handler_command_smoke.jsonl` output.
- Tests/rules locking that no route handler call, RouteProxyRuntime preparation,
  writer permit request, frame write, Scheduler modification, EventBus
  instantiation, GitHub API, network, conversion, inference, SQL, Qdrant, or
  VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No route handler execution.
- No ControlProxy/RouteProxy frame write.
