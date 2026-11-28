# Changelog — 0107 ControlProxy graph root alignment

- Added a root-attached runtime overlay for ControlProxy / RouteRuntimeManager.
- Added a graph integration note explaining how the runtime overlay relates to
  `doc/docs/architecture/00_global.dot` and the existing Scheduler and Context
  graph families.
- Locked that the runtime overlay is not an isolated graph.
- Locked that Scheduler, PolicyEngine, PriorityQueue, Dispatcher, Handler,
  Specialist, EventBus, Context and RouteRuntimeManager keep separate roles.
- Locked that route mmap/eventfd is data plane, not EventBus.
- Added rule tests for the graph-root alignment.
- No runtime code, CLI, daemon, watcher, Scheduler, Dispatcher, PolicyEngine,
  PriorityQueue or EventBus change.
