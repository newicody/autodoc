# Phase 0176 Test Report — GitHub artifact dataset bus observation bridge

Status: prepared.

Scope:
- Operational bridge to existing `event.bus/context.bus` JSONL observation files.
- Reuses `runtime.shm_runtime_schema.EventBusMessage`.
- Reuses `runtime.shm_runtime_schema.ContextBusMessage`.
- No new bus.
- No Scheduler modification.
- No VisPy direct write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/context/test_github_artifact_dataset_bus_observation_0176.py \
  tests/tools/test_project_github_artifact_dataset_bus_observation_0176.py \
  tests/rules/test_github_artifact_dataset_bus_observation_bridge_0176_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
