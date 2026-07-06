# 0089 — route write/notify/drain

This patch adds the first end-to-end producer/consumer route primitive after the
0088 Scheduler handler boundary.

It composes existing runtime primitives:

```text
MmapFixedSlotRoute.write_message()
-> RouteNotifier.notify()
-> selectors.DefaultSelector
-> RouteNotifier.drain()
-> MmapFixedSlotRoute.drain()
```

## Scope

- Add `runtime.route_write_notify_drain` with importable producer and consumer
  helper functions.
- Add a runtime test that writes a `RouteMessage` into the file-backed mmap
  route, notifies through the pipe backend, observes readiness through a
  selector, drains the notification counter and drains the route frame.
- Add a rule test and architecture note locking the 0089 boundary.

## Non-goals

- No CLI.
- No daemon, service or OpenRC integration.
- No resident watcher.
- No Scheduler loop change.
- No PriorityQueue, Dispatcher or Component contract change.
- No policy/zone/scope bypass.
- No lease authority change.
- No live mmap resize.
- No Recorder/journal ingestion yet.
- No route generation g2/g3 yet.
- No drain/closed cleanup yet.
- No Qdrant, LLM or OpenVINO path.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_write_notify_drain.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## code_rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0089 adds a real importable producer write, notifier notification, selector readiness, and mmap drain path without adding a CLI, daemon, watcher, Scheduler-loop change, policy bypass, backend dependency, or live resize.
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
