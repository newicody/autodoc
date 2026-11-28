# Changelog — 0106 EventBus / data plane boundary

- Locked EventBus as observation only.
- Locked route mmap/eventfd as data plane, not EventBus.
- Rejected ControlProxyBus, RouteBus and VisualizationBus concepts.
- Documented RouteMessageJournal as drained-message journal, not EventBus.
- Added runtime `.dot` overlay for the boundary.
- Added rule tests to prevent terminology drift.
- No runtime code, no CLI, no daemon, no watcher and no Scheduler/Dispatcher changes.
