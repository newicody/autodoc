# 0114-r2 — Context variation core contract

This patch replaces the rejected linear 0114 direction with a trajectory-based
context variation contract.

It adds pure immutable contracts for:

- `ContextVariationObjective`
- `ContextVariationAxis`
- `ContextTrajectory`
- `ContextVariantCandidate`
- `ContextExplorationPlan`
- `ContextExplorationResult`
- `ContextReductionPlan`
- `InferenceContextDraft`

Scope:

- no MVTC runtime;
- no SQL/Qdrant/OpenVINO/LLM runtime import;
- no new EventType;
- no Scheduler/Dispatcher/Policy/Queue/EventBus changes;
- no CLI, daemon, watcher, or service.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_context_variation_core_contract.py
PYTHONPATH=src:. pytest -q tests/rules/test_context_variation_core_contract_0114_r2_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
