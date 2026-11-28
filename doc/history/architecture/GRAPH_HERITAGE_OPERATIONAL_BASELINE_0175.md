# 0175 — Graph heritage and operational baseline

## Decision

0175 explicitly avoids merging or replacing the old global graph.

The old DOT graphs remain valuable as heritage: they preserve ideas,
orientation, roadmap memory, historical design attempts, and inspiration for
later architecture work.

The immediate operational baseline is the rebuilt 0174 graph draft and its
subgraphs, combined with the current working code surfaces and the validated
0162..0174 chain.

## Two-layer graph model

0175 locks a two-layer model:

### Heritage layer

The heritage layer contains older graphs, roadmap notes, stale-doc sections,
long-term ideas, and orientation traces.

Heritage is useful for inspiration and future design, but it is not the short
term execution plan.

### Operational baseline layer

The operational baseline layer contains what we can act on now:

- existing runtime bus observation surfaces,
- existing scheduler route/handler/handshake surfaces,
- GitHub artifact/dataset chain as currently planned,
- SQL durable store and Qdrant projection split,
- ControlProxy/RouteProxy runtime boundaries,
- 0174 rebuilt graph draft and maintained subgraphs.

This layer is the source for immediate patches.

## Rule for old graphs

Old graphs should not be deleted just because they are stale.

They should be marked, interpreted, and kept as:

```text
heritage
orientation
inspiration
historical
stale-doc
future-idea
```

They must not silently override the operational baseline.

## Immediate development direction

The next implementation work should not be a graph merge. It should continue
from the stable base:

```text
GitHub artifacts / dataset
-> scheduler-addressable work or bus-compatible observation facts
-> existing event.bus/context.bus
-> bus_visualization_adapter
-> DOT/VisPy/browser projection
```

and:

```text
Scheduler / policy / zone
-> scheduler route handshake / adapter / handler
-> ControlProxy / RouteProxy when needed
-> observation facts
```

## Merge later

A future merge into `00_global.dot` is allowed only later, after the operational
chain is stable enough and after the old graph has been reviewed as heritage.

The merge must preserve inspirational roadmap content instead of flattening it.

## Non-goals

- No direct `00_global.dot` merge.
- No graph deletion.
- No runtime implementation.
- No Scheduler modification.
- No VisPy renderer.
- No new EventBus.
- No parallel bus.
- No GitHub API.
- No network.
- No conversion execution.
- No inference.
- No SQL/qdrant write.

## Exact rule-test lock phrases — 0175

ideas, orientation, roadmap memory, historical design attempts, and inspiration.

## Exact rule-test lock phrases — 0175

ideas, orientation, roadmap memory, historical design attempts, and inspiration.
