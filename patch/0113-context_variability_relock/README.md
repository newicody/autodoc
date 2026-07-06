# 0113-context_variability_relock

Relock architecture around context variability and rapid solution production.

## Scope

This is a docs/graph/rules patch only. It recenters the project on:

```text
ContextRequest -> ContextCollector -> ContextVariant[] -> ContextReducer -> GlobalContextSnapshot -> InferenceContext -> specialist / LLM / MVTC -> solution candidate / feedback
```

It explicitly rejects the CapabilityRequest/security-first direction for the active 0113 path and places SQL/Qdrant/OpenVINO/LLM as context construction, projection, embedding and specialist/enrichment capabilities behind the kernel path.

## Non-goals

- no runtime code
- no CLI
- no daemon/service/OpenRC
- no watcher
- no Scheduler.run modification
- no Dispatcher/PriorityQueue/PolicyEngine/EventBus modification
- no Qdrant/OpenVINO/LLM import
- no SQL runtime code yet
- no second bus

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_context_variability_relock_0113_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
