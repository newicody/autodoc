# 0122 — Passive context graph export

0122 adds a passive, importable context graph exporter.  It is a visualization
contract, not a runtime observer.

Core flow:

```text
GitHubProjectScenarioPacket -> ContextGraphSnapshot -> DOT export
```

Required architectural phrases:

- Passive context graph export reads contracts only; it does not observe live events.
- No watcher/service/EventBus subscription in ContextGraphExport.
- SQLContextStore is durable context authority.
- Qdrant is vector projection and retrieval, not context authority.
- OpenVINO produces embeddings behind adapter.
- LLM is specialist producer, not context authority.
- Scheduler orchestrates context exploration jobs; it does not build graphs itself.
- MVTC remains future, not runtime in 0122.

## Why this exists

The previous patches created pure contracts for context variability, planning,
SQL authority, hydration, OpenVINO embedding boundaries, Qdrant projection,
LLM specialist candidates, and GitHub Project publication packets.  0122 adds a
read-only graph layer so those contracts can be inspected as a deterministic
DOT export.

## What it does

`src/context/context_graph_export.py` can build a `ContextGraphSnapshot` from a
`GitHubProjectScenarioPacket` and render it to plain DOT text.  The graph shows:

1. GitHub artifact as workflow surface;
2. SourceCandidate SQL import contract;
3. SQLContextStore authority;
4. ContextVariationObjective;
5. ContextExplorationPlan;
6. Qdrant projection/retrieval as rebuildable projection;
7. LLMSpecialistResult;
8. GitHubProjectPublication;
9. future GitHub adapter posting result.

## What it does not do

It does not import Graphviz, NetworkX, VisPy, Qdrant, OpenVINO, PostgreSQL,
HTTP clients, sockets, Scheduler, Dispatcher, PolicyEngine, EventBus, or
RouteRuntimeManager.  It does not watch files, subscribe to events, start a
service, or claim runtime authority.

The output is a passive document/export surface only.
