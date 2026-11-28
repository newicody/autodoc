# 0090 — Route message journal

Status: 0090 implementation.

0090 adds Recorder/journal ingestion for RouteMessage objects drained from an active route. It consumes the 0089 `RouteSelectorDrainResult`, turns each drained `RouteMessage` into a deterministic JSONL journal record, and exposes `write_drained_route_messages_journal` plus `load_route_message_journal` as importable functions.

## Operational path

```text
producer write mmap
-> notifier.notify
-> consumer selector/drain
-> RouteSelectorDrainResult
-> route message journal records
-> deterministic JSONL journal
```

The journal is an audit surface. The journal records are facts, not commands.

## Boundaries

No daemon, no service, no OpenRC.
No resident watcher.
No CLI.
No direct mmap read.
No notifier ownership.
No Scheduler loop modification.
Scheduler/policy/zone remain upstream authorities.
ControlProxy does not decide security.

0090 performs no authorization, no lease grant, no policy decision, no live mmap resize, no route generation g2/g3, no drain/closed cleanup, no inter-process lock, no Qdrant, no LLM, no OpenVINO.

## Why this belongs before 0091

Before route generations g2/g3 are introduced, drained messages need a deterministic journal projection. This gives the next phases a replayable fact stream without changing the live route layout.
