# 0095 — route generation locked materializer

This patch adds an importable locked façade around the route generation
materializer.

It composes:

```text
0094 acquire_route_generation_lock()
0091-r2 materialize_route_generation_candidate()
```

Operational path:

```text
with acquire_route_generation_lock(controlfs_root, route_id):
    load -> verify -> materialize -> persist
```

Boundaries:

```text
No CLI.
No OpenRC service and no resident daemon.
No watcher.
No Scheduler.run() modification.
No PriorityQueue, Dispatcher or Component tick contract modification.
No live mmap resize.
ControlProxy does not decide security.
Scheduler/policy/zone remain the authority.
Not /dev/shm-only.
standard library only.
```

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_locked_materializer.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_locked_materializer_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
