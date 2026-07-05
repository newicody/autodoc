# Changelog 0129 — RouteProxy flow-control contract

Added:

- `src/context/route_proxy_flow_control_contract.py`
- runtime tests for RouteProxy leases, writer permits, context fences, pressure signals, and observation facts
- rule tests for Scheduler/RouteProxy/EventBus/SQL/Qdrant/OpenVINO boundaries
- architecture docs and DOT graph

No Scheduler, Dispatcher, Queue, Policy, EventBus, RouteRuntimeManager, Qdrant client, OpenVINO runtime, PostgreSQL driver, GitHub client, daemon, watcher, or socket was added.
