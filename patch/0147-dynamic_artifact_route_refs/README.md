# 0147 — Dynamic artifact route refs

This patch derives Scheduler command refs and RouteProxy request/result route refs from typed artifact inputs.

It reuses:

- `src/context/artifact_intake_contract.py`
- `tools/run_local_artifact_vector_indexing_runner.py`
- `tools/run_scheduler_vector_indexing_smoke.py`
- existing RouteProxyRuntime and Scheduler route handler surfaces

It does not create a new orchestrator, does not modify `Scheduler.run()`, and does not introduce new OpenVINO/Qdrant adapters.

Validation used during patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_dynamic_artifact_route_refs_0147.py tests/rules/test_dynamic_artifact_route_refs_0147_rule.py
PYTHONPATH=src:. pytest -q tests/tools/test_artifact_intake_contract_0146.py tests/tools/test_local_artifact_vector_indexing_runner_0145.py tests/tools/test_dynamic_artifact_route_refs_0147.py
PYTHONPATH=src:. pytest -q tests/rules/test_artifact_intake_contract_0146_rule.py tests/rules/test_local_artifact_vector_indexing_runner_0145_rule.py tests/rules/test_dynamic_artifact_route_refs_0147_rule.py
```
