# Changelog 0130 — RouteProxy runtime minimal

Added a first live local RouteProxy runtime step:

- `src/runtime/route_proxy_runtime_minimal.py`
- runtime tests for prepare/permit/write/read/stale/facts
- rule tests for the runtime membrane
- architecture docs and DOT graph
- `doc/code-rules/0130_route_proxy_runtime_rule.md`

No Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, SQL, OpenVINO, Qdrant, GitHub, service, daemon, watcher, network client, or backend runtime is introduced.
