# 0088-controlproxy_scheduler_handler

Patch 0088 adds a concrete importable Scheduler/Dispatcher handler for the
ControlProxy Scheduler route-request adapter from 0086.

## Apply

```bash
unzip -o /mnt/data/0088-controlproxy_scheduler_handler.zip -d .
python apply_patch_queue.py --patch 0088-controlproxy_scheduler_handler --dry-run
python apply_patch_queue.py --patch 0088-controlproxy_scheduler_handler --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_scheduler_handler.py
PYTHONPATH=src:. pytest -q tests/rules
```

## Scope

- Adds a handler boundary only.
- Calls `handle_scheduler_route_request()` instead of duplicating route logic.
- No CLI.
- No daemon/service/OpenRC.
- No Scheduler loop modification.
- No policy/zone/scope bypass.
