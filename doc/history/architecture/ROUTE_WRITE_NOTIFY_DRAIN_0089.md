# 0089 — Route write/notify/drain E2E primitive

Status: 0089 implementation.

0089 validates the first real end-to-end hot-route primitive after the Scheduler
handler boundary from 0088:

```text
producer write mmap + notifier.notify + consumer selector/drain
```

The importable implementation is intentionally tiny:

```text
MmapFixedSlotRoute.write_message()
-> RouteNotifier.notify()
-> selectors.DefaultSelector
-> RouteNotifier.drain()
-> MmapFixedSlotRoute.drain()
```

## Scope

The module logic is importable and testable. It adds no CLI because this is not
yet a real operator boundary. It adds no daemon because the route remains driven
by explicit calls from the current execution path.

No daemon, no service, no OpenRC.

No resident watcher, no sleep loop, no poll loop.

No CLI. CLI only when it is a real operator boundary.

Scheduler/policy/zone remain upstream authorities. ControlProxy does not decide security. The route write/notify/drain primitive only transports an already accepted RouteMessage across the already materialized route.

## Non-goals kept explicit

0089 does not add:

- Scheduler loop modification
- policy decision logic
- zone/scope bypass
- route lease authority
- live mmap resize
- route generation g2/g3
- Recorder/journal ingestion
- drain/closed cleanup
- inter-process locks
- POSIX shm_open
- mandatory /dev/shm
- semaphores
- futex
- Qdrant
- LLM
- OpenVINO
- NetworkBridge
- HardwareBridge
- VisPy/browser adapters


Compatibility guard phrases for rule tests:

```text
no live mmap resize
no Recorder/journal ingestion
no route generation g2/g3
no drain/closed cleanup
no Qdrant, no LLM, no OpenVINO
```

So the next phases remain ordered:

```text
0090 Recorder/journal ingestion of drained RouteMessage values
0091 route generation g2/g3 for update/resize without live resize
0092 drain/closed cleanup
0093 VisPy/browser projection from event.bus/context.bus facts
```

## code_rule review block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0089 adds a real importable producer/consumer route primitive around existing mmap and notifier surfaces without adding a CLI, daemon, watcher, Scheduler-loop change, policy bypass, backend dependency, or live resize.
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
