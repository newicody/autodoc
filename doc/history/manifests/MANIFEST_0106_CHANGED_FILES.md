# Manifest 0106 — EventBus / data plane boundary

## Added

```text
doc/architecture/EVENTBUS_DATAPLANE_BOUNDARY_0106.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0106.md
doc/docs/architecture/runtime/96_eventbus_dataplane_boundary.dot
doc/CHANGELOG_0106_EVENTBUS_DATAPLANE_BOUNDARY.md
doc/manifests/MANIFEST_0106_CHANGED_FILES.md
tests/rules/test_eventbus_dataplane_boundary_0106_rule.py
PHASE0106_TEST_REPORT.md
```

## Intent

0106 locks the boundary between the existing EventBus observation path and the
route mmap/eventfd data plane.

## Guardrails

```text
No CLI
No OpenRC service and no resident daemon
No watcher
No Scheduler.run() modification
No Dispatcher business logic
No PriorityQueue modification
No PolicyEngine expansion into business logic
No ControlProxy global priority management
No ControlProxyBus
No RouteBus
No VisualizationBus
No bus created by ControlProxy
No bus created by RouteRuntimeManager
No bus owned by visualization adapters
No mmap/eventfd command bus
Route mmap/eventfd = data plane, not EventBus
EventBus = observation only
```
