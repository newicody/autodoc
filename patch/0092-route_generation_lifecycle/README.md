# 0092 — route generation lifecycle

This patch adds importable lifecycle helpers for ControlProxy route generations:

```text
candidate -> active -> draining -> closed -> cleanup closed generation
```

It consumes the generation table from 0091-r2 and provides explicit functions for
activation, draining, closing, and cleanup of runtime files belonging to closed
generations only.

## Scope

- Adds `src/runtime/route_generation_lifecycle.py`.
- Adds runtime tests for active/draining/closed cleanup and invalid transitions.
- Adds a rule test that locks no-CLI/no-daemon/no-live-resize boundaries.
- Adds phase documentation, manifest, and test report.

## Non-goals

- No CLI.
- No OpenRC service or resident daemon.
- No watcher/inotify loop.
- No Scheduler.run(), PriorityQueue, Dispatcher, or Component contract changes.
- No policy/zone/scope decision in ControlProxy.
- No live mmap resize.
- No cleanup of candidate, active, or draining generations.
- No inter-process locks yet.
- No Qdrant, LLM, OpenVINO, network, or GitHub API.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_lifecycle.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_lifecycle_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
