# 0122-context_graph_export

Adds a passive context graph export boundary.

The patch introduces `src/context/context_graph_export.py`, which builds a
`ContextGraphSnapshot` from a `GitHubProjectScenarioPacket` and renders a
plain deterministic DOT export. It is a visualization/documentation contract,
not a live observer.

It does not import Graphviz, NetworkX, VisPy, Qdrant, OpenVINO, PostgreSQL,
HTTP clients, sockets, Scheduler, Dispatcher, PolicyEngine, EventBus, or
RouteRuntimeManager.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_context_graph_export.py
PYTHONPATH=src:. pytest -q tests/rules/test_context_graph_export_0122_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
