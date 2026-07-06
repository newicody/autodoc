# 0130 — RouteProxy runtime minimal

First live local data-plane step for RouteProxy.

Adds a small runtime that can:

- prepare a route root under `/dev/shm/autodoc/routes` by default;
- allow explicit non-`/dev/shm` roots only for tests;
- grant or deny writer permits;
- write route frames atomically;
- read route frames;
- mark route frames stale when context generation advances;
- persist observation-ready facts.

Boundary lock:

- Scheduler remains the orchestrator.
- RouteProxy runtime is a data-plane executor, not an orchestrator.
- `Scheduler.run()` is not modified.
- No mount table scan is performed.
- EventBus receives observation-ready facts, not payload commands.
- SQLContextStore remains durable authority.
- E5/OpenVINO and Qdrant are not touched by 0130.
- A supplemental code rule is added in `doc/code-rules/0130_route_proxy_runtime_rule.md`.

Apply:

```bash
python apply_patch_queue.py --patch 0130-route_proxy_runtime_minimal --dry-run
python apply_patch_queue.py --patch 0130-route_proxy_runtime_minimal --commit --push
```

Validate:

```bash
PYTHONPATH=src:. python -m compileall -q src tests
PYTHONPATH=src:. pytest -q tests/runtime/test_route_proxy_runtime_minimal.py tests/rules/test_route_proxy_runtime_minimal_0130_rule.py
```
