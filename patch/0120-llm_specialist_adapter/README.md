# 0120 — LLM specialist adapter

Adds a pure specialist boundary after `InferenceContextDraft` and SQL hydration.

Apply:

```bash
python apply_patch_queue.py --patch 0120-llm_specialist_adapter --dry-run
python apply_patch_queue.py --patch 0120-llm_specialist_adapter --commit --push
```

Validate:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_llm_specialist_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_llm_specialist_adapter_0120_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Scope:

- adds `src/inference/llm_specialist_adapter.py`;
- consumes `InferenceContextDraft` and `SqlHydratedContextBundle`;
- uses an injected executor for actual LLM/specialist execution;
- emits traceable solution candidates with `evidence_refs` and optional `action_refs`;
- does not modify Scheduler, Dispatcher, PolicyEngine, EventBus, Queue, or RouteRuntimeManager;
- does not import LLM SDKs, HTTP clients, sockets, Qdrant, OpenVINO, or PostgreSQL drivers.
