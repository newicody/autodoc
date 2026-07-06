# 0093-r2 — existing bus visualization adapter

This patch replaces the rejected 0093 direction.

It adds an importable read adapter that attaches to an existing `EventBus` via
`event_bus.subscribe()` and reads an existing context snapshot source. It does
not instantiate `EventBus`, does not create a parallel bus, and does not launch
VisPy/browser runtime code.

## Apply

```bash
unzip -o /mnt/data/0093-r2-existing_bus_visualization_adapter.zip -d .
python apply_patch_queue.py --patch 0093-r2-existing_bus_visualization_adapter --dry-run
python apply_patch_queue.py --patch 0093-r2-existing_bus_visualization_adapter --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_bus_visualization_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_bus_visualization_adapter_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Boundaries

- No CLI.
- No daemon, OpenRC service, or resident watcher.
- No Scheduler loop modification.
- No policy/zone/scope bypass.
- No ControlProxy security decision.
- No Qdrant, LLM, OpenVINO, network, VisPy dependency, or browser launch.
- EventBus remains observation only.
- Events/bus facts are facts, not commands.
