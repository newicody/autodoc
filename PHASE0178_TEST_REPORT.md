# Phase 0178 Test Report — Context bus scheduler intake reader

Status: prepared.

Scope:
- Reads existing `context.bus.jsonl`.
- Reuses `ContextBusMessage.from_mapping`.
- Filters topic `github.artifact_dataset.context`.
- Filters payload schema `missipy.github_artifact.dataset_context.v1`.
- Builds scheduler intake through the 0177 builder.
- No Scheduler modification.
- No EventBus instantiation.
- No route handler call.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/context/test_github_artifact_context_bus_scheduler_intake_0178.py \
  tests/tools/test_build_github_artifact_scheduler_intake_from_context_bus_0178.py \
  tests/rules/test_context_bus_scheduler_intake_reader_0178_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
