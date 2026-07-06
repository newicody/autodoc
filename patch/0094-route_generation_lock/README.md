# 0094-route_generation_lock

Adds an importable ControlProxy route generation inter-process lock.

The patch introduces `src/runtime/route_generation_lock.py`, a small
`fcntl.flock`-backed context manager for the ControlFS sidecar lock path:

```text
active/routes/<route_id>/generation.lock
```

The lock protects the generation table critical section but does not allocate
routes itself. It does not add a CLI, OpenRC service, resident daemon, watcher,
network path, Scheduler modification, Qdrant, LLM or OpenVINO integration.

## Apply

```bash
unzip -o /mnt/data/0094-route_generation_lock.zip -d .
python apply_patch_queue.py --patch 0094-route_generation_lock --dry-run
python apply_patch_queue.py --patch 0094-route_generation_lock --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_lock.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_lock_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
