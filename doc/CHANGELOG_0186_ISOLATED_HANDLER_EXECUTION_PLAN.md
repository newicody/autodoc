# Changelog — 0186 Isolated handler execution plan

## Added

- Isolated handler execution planning from 0185 command-builder smoke output.
- AST/text resolver for `RouteProxyRuntimePolicy` and RouteProxyRuntime surface
  availability.
- Optional `isolated_handler_execution_plan.jsonl` output.
- Tests/rules locking that no RouteProxyRuntime import, preparation, writer
  permit request, frame write, handler call, Scheduler modification, EventBus
  instantiation, GitHub API, network, conversion, inference, SQL, Qdrant, or
  VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No route handler execution.
- No RouteProxyRuntime preparation.
- No ControlProxy/RouteProxy frame write.
