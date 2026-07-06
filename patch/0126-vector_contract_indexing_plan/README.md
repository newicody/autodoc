# 0126 — Vector contract indexing plan

This patch locks the vector contract indexing direction:

- one Qdrant instance with multiple role-oriented collections, not one database per specialist;
- SQL-owned specialist instruction contracts and human representation contracts;
- E5/OpenVINO as embedding only behind adapter;
- Qdrant as projection/retrieval only, not decision authority;
- specialist outputs indexed as machine_result plus human_representation references;
- Scheduler remains the deliberation orchestrator;
- GitHub remains artifact exchange only.

No Scheduler.run(), Dispatcher, Queue, PolicyEngine, EventBus, RouteRuntimeManager, GitHub client, HTTP/socket client, Qdrant client, OpenVINO runtime, PostgreSQL driver, LLM SDK, service, daemon, watcher, or VisPy renderer is modified.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_vector_contract_indexing_plan.py
PYTHONPATH=src:. pytest -q tests/rules/test_vector_contract_indexing_plan_0126_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
