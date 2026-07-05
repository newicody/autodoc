# Changelog — 0101 ControlProxy simplification lock

## Added

- Architecture lock for Scheduler, PolicyEngine, PriorityQueue, Dispatcher, Handler, Specialist branch, ControlProxy/RouteRuntimeManager, EventBus, and route data plane responsibilities.
- Runtime overlay DOT showing the simplified root-attached direction.
- Operational roadmap from 0101 to 0107.
- Rule test that prevents the locked simplification from being silently weakened.

## Changed

- The previously proposed scheduler-like ControlProxy route coordinator direction is rejected as the next code direction.
- Future ControlProxy runtime code should converge toward a narrow RouteRuntimeManager.

## Not changed

- No runtime code is changed.
- No scheduler loop is changed.
- No dispatcher implementation is changed.
- No policy implementation is changed.
- No queue implementation is changed.
- No bus implementation is changed.
