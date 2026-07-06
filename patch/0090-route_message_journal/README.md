# 0090 — route message journal

This patch adds the first real Recorder/journal ingestion boundary for RouteMessage objects drained from an active route.

It consumes the 0089 `RouteSelectorDrainResult`, converts each drained `RouteMessage` into a deterministic JSONL record, and exposes importable functions only.

## Scope

- Add `runtime.route_message_journal`.
- Add runtime tests for write/notify/drain -> journal -> load.
- Add rule tests that lock the phase boundary.
- Add architecture note, manifest, and phase report.

## Explicit non-scope

- No CLI.
- No daemon/service/OpenRC.
- No resident watcher.
- No Scheduler loop change.
- No PriorityQueue or Dispatcher change.
- No Component.tick/yield/reply contract change.
- No policy/zone/scope bypass.
- No direct mmap read in the journal module.
- No notifier ownership.
- No live mmap resize.
- No route generation g2/g3.
- No drain/closed cleanup.
- No Qdrant, LLM, or OpenVINO dependency.
