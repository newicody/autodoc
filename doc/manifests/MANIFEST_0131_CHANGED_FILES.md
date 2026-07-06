# Manifest 0131 — changed files

- src/runtime/scheduler_route_handler_minimal.py
- tests/runtime/test_scheduler_route_handler_minimal.py
- tests/rules/test_scheduler_route_handler_minimal_0131_rule.py
- doc/architecture/SCHEDULER_ROUTE_HANDLER_MINIMAL_0131.md
- doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0131.md
- doc/code-rules/0131_scheduler_route_handler_rule.md
- doc/docs/architecture/runtime/131_scheduler_route_handler_minimal.dot
- doc/CHANGELOG_0131_SCHEDULER_ROUTE_HANDLER_MINIMAL.md
- doc/manifests/MANIFEST_0131_CHANGED_FILES.md
- PHASE0131_TEST_REPORT.md

Boundary note: 0131 adds a minimal handler/executor bridge only. It does not edit the kernel loop, Scheduler.run, Dispatcher, Queue, PolicyEngine, EventBus, OpenVINO, Qdrant, PostgreSQL, GitHub, daemon, watcher, or network clients.
