# 0147-r1 — Scheduler run boundary phrase fix

This patch fixes a rule-test false positive introduced by 0147.

0147 added a human boundary line in `tools/run_scheduler_vector_indexing_smoke.py` containing the literal text `Scheduler.run()`. Existing 0143/0144 rule tests forbid that exact substring in the tool body to prevent accidental Scheduler loop coupling.

This patch only changes the human-facing boundary phrase to avoid the forbidden literal while preserving the intended meaning.

It does not change behavior, routing, refs, OpenVINO, Qdrant, Scheduler, or RouteProxyRuntime.

Suggested validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_scheduler_vector_indexing_smoke_0143_rule.py tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py tests/rules/test_dynamic_artifact_route_refs_0147_rule.py
PYTHONPATH=src:. pytest -q tests/rules
```
