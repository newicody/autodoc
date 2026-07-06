# 0097 — ControlProxy graph alignment

This patch integrates the route/runtime placement architecture into a root graph
instead of keeping it as an isolated phase diagram.

Scope:

- adds a root `.dot` graph with subgraphs for policy/zone, ControlProxy/ControlFS,
  runtime surfaces, and future extensions;
- documents the ControlProxy/ControlFS bounded subsystem shape;
- documents that Dispatcher remains the handler boundary;
- documents that `Scheduler.run()` remains locked until an explicit loop-extension
  design is accepted;
- adds rule tests to keep the graph and wording stable.

Out of scope:

- no Scheduler, Queue, Dispatcher, or Component contract modification;
- no ControlProxy runtime code change;
- no CLI, service, daemon, watcher;
- no NetworkBridge or HardwareBridge implementation;
- no Qdrant, LLM, or OpenVINO path.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_graph_alignment_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
