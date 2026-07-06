# 0091-r2 — route generation table

This patch implements the ControlProxy-side route generation table proposed in
review:

```text
route_id -> current_generation
```

It materializes a new fixed-slot mmap route only when the persisted table says
that the requested generation is the next allocatable generation. It writes:

```text
active/routes/<route_id>/generation_state.json
active/routes/<route_id>/generations/gN/status.json
routes/<route_id>@gN/ring.bin
```

It deliberately does not resize any existing mmap route in place. g1 remains its
own `ring.bin`; g2/g3 are separate route handles.

## Scope

- Adds `src/runtime/route_generation_table.py`.
- Adds runtime tests for g1/g2 materialization and stale allocation rejection.
- Adds a rule test that locks the no-CLI/no-daemon/no-live-resize boundaries.
- Adds phase documentation, manifest, and test report.

## Non-goals

- No CLI.
- No OpenRC service or resident daemon.
- No watcher/inotify loop.
- No Scheduler.run(), PriorityQueue, Dispatcher, or Component contract changes.
- No policy/zone/scope decision in ControlProxy.
- No live mmap resize.
- No inter-process locks yet.
- No Qdrant, LLM, OpenVINO, network, or GitHub API.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_table.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_table_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
