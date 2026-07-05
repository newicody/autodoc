# 0109 — ControlProxy compatibility wrapper cleanup

- Added an importable compatibility-wrapper registry for legacy ControlProxy helpers.
- Marked `prepare_route_for_scheduler` and `handle_scheduler_route_request` as compatibility wrappers.
- Locked the replacement direction as `Handler -> RouteRuntimeManager`.
- Added docs, graph and rule tests preventing a scheduler-like ControlProxy coordinator or bus duplication.
- No Scheduler, Dispatcher, PriorityQueue, PolicyEngine or EventBus code is modified.
