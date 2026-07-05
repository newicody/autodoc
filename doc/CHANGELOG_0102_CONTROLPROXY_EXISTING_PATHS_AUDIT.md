# Changelog — 0102 ControlProxy existing paths audit

## Added

- Audit of existing Scheduler, Dispatcher, PolicyEngine, PriorityQueue, Handler, Specialist, ControlProxy, EventBus, Context, Recorder, and runtime-route paths.
- Classification of current ControlProxy helpers into compatibility-wrapper candidates, runtime primitives, data-plane primitives, observation readers, and future integration points.
- Risk register for duplicated concepts before `RouteRuntimeManager` is introduced.
- Root-attached DOT overlay that shows the audit classification without presenting future runtime wiring as already implemented.
- Rule test that locks the audit intent before 0103.

## Changed

- The next code direction is clarified: 0103 introduces a narrow `RouteRuntimeManager`; it does not introduce a scheduler-like ControlProxy coordinator.

## Not changed

- No runtime code is changed.
- No scheduler loop is changed.
- No dispatcher implementation is changed.
- No policy implementation is changed.
- No queue implementation is changed.
- No EventBus implementation is changed.
