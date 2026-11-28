# Changelog — 0194 Isolated route pipeline promotion plan

## Added

- Promotion planning tool from accepted isolated baseline registry.
- Controlled target label: `controlled-dev-routeproxy-smoke`.
- Explicit `target_runtime_root` and `target_isolated_runtime_root` planning.
- Preconditions for future controlled dev smoke.
- Tests/rules locking that no runtime import, handler call, RouteProxy runtime
  call, frame write, Scheduler modification, EventBus instantiation, GitHub API,
  network, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No runtime execution.
- No promotion execution.
- No new runtime handler.
- No Scheduler.run modification.
- No production route write.
