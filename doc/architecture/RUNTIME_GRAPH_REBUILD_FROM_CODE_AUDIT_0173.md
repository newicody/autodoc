# 0173 — Runtime graph rebuild from code audit

## Problem

The architecture DOT graphs, graph documentation, and some changelogs are not
fresh enough to be used as the sole source of truth.

`doc/docs/architecture/00_global.dot` is still useful as a historical master
graph, but it must not be trusted blindly. It contains older roadmap notes and a
large accumulated structure. Recent work introduced GitHub artifact/dataset,
bus/VisPy, scheduler route, Qdrant/SQL rehydration, and patch-queue decisions
that are not all reflected with equal freshness.

The graph rebuild must therefore be deduced from:

1. code surfaces that exist and pass tests,
2. rule tests and manifests,
3. applied patch queue history and commits,
4. the planned 0162..0172 chain,
5. architecture docs and changelogs only as supporting context,
6. stale DOT files only as historical input.

## Decision

0173 does not rewrite the global graph yet.

0173 locks the method for rebuilding the global graph and subgraphs from the
current code and the validated direction.

A future patch may update `doc/docs/architecture/00_global.dot`, but only after
an exact local audit of the current file and only if the patch also updates or
adds the matching subgraphs.

## Existing code surfaces that anchor the rebuilt graph

The rebuilt graph must start from existing working surfaces, not from desired
future blocks.

### Runtime bus and VisPy/browser observation

- `src/runtime/bus_visualization_adapter.py`
- `src/runtime/shm_runtime_schema.py`

The current rule is:

```text
event.bus/context.bus
-> existing bus visualization adapter
-> DOT/VisPy/browser projection
```

VisPy/browser must not become a writer target for GitHub tools or dataset tools.

### Scheduler / route / handler surfaces

- `src/runtime/scheduler_route_handshake.py`
- `src/runtime/scheduler_route_adapter.py`
- `src/runtime/controlproxy_scheduler_handler.py`
- `src/runtime/scheduler_route_handler_minimal.py`

The current rule is:

```text
Scheduler/policy/zone
-> authorized scheduler route request
-> scheduler route handshake/adapter/handler
-> observable event.bus/context.bus facts
```

The Scheduler remains the orchestrator. EventBus remains observation-only.

### ControlProxy / RouteProxy data plane

The graph must keep the ControlProxy/RouteProxy boundary separated from
business authority. RouteProxy/ControlProxy may expose fast runtime facts,
leases, route frames, and observation files, but they do not decide policy.

### Vector / SQL / Qdrant recall chain

The graph must preserve the durable/projection split:

```text
SQL store = durable authority/provenance/rehydration
Qdrant = projection/search/recall index
sql_ref = bridge from vector hit back to durable SQL record
```

### GitHub artifact and dataset chain

The rebuilt graph must include the external artifact flow as an exchange layer,
not as the Autodoc internal runtime bus:

```text
GitHub Project / issue / idea repo
-> GitHub Action ticket artifact
-> Copilot preliminary opinion artifact
-> read-only artifact fetch
-> configured server dataset
-> raw/index/history/queue
-> scheduler-addressable work or bus-compatible observation facts
-> local inference/conversion later
-> publication/review artifacts back to GitHub later
```

GitHub remains workflow/exchange/validation surface. The local/server dataset
and SQL store remain local authority surfaces.

## Rebuilt global chain

The canonical chain to represent is:

```text
External idea source
-> GitHub Project / issue
-> GitHub Actions artifacts
-> server dataset sync
-> dataset raw/index/history/queue
-> scheduler route/intake surfaces
-> ControlProxy/RouteProxy runtime path when needed
-> OpenVINO/E5 embedding and specialist work when scheduled
-> Qdrant projection/search
-> SQL durable hydration
-> result/review/publication artifact
-> GitHub validation surface
```

Observation chain:

```text
runtime facts
-> event.bus/context.bus
-> bus_visualization_adapter
-> DOT activity graph support
-> VisPy/browser view
```

## Required subgraphs

The refresh must produce or align at least these subgraphs:

1. `global`: the current top-level architecture.
2. `runtime-bus`: EventBus/context bus, SHM schema, bus visualization adapter.
3. `scheduler-route`: Scheduler route handshake/adapter/handler.
4. `github-artifact-dataset`: GitHub Action artifacts to server dataset.
5. `vector-sql-qdrant`: embedding, Qdrant projection, SQL rehydrate.
6. `controlproxy-routeproxy`: leases, frames, route data plane, observation facts.
7. `activity-graph-vispy`: DOT support, titles, zoom, navigation, view modes.
8. `docs-provenance`: patch queue, manifests, rules, changelogs, stale-doc status.

## View modes to preserve

The activity graph contract from 0172 remains valid:

- `architecture`
- `runtime`
- `artifact`
- `scheduler`
- `bus`
- `score`
- `population`
- `debug`

## Status and freshness model

Graph nodes and subgraphs should carry freshness metadata where possible:

- `current`
- `validated`
- `partial`
- `planned`
- `historical`
- `superseded`
- `deprecated`
- `blocked`
- `stale-doc`

Use `abandoned` only when explicitly proven.

## Changelog hole policy

Changelogs are useful but incomplete. A missing changelog entry must not erase a
working code surface from the rebuilt graph.

When changelogs and code disagree, code plus passing tests wins. The stale
changelog is then marked as a documentation gap.

## 00_global.dot policy

`00_global.dot` should be refreshed after this audit, but not blindly.

The next update must:

- inspect the exact current local `00_global.dot`,
- preserve useful historical ROADMAP notes,
- mark stale areas rather than deleting them silently,
- add missing current surfaces from working code,
- link each major node to a maintained subgraph,
- avoid claiming runtime execution that does not exist,
- avoid turning DOT into authority.

## Non-goals

- No runtime implementation.
- No graph renderer implementation.
- No VisPy rendering change.
- No Scheduler modification.
- No GitHub API.
- No network.
- No conversion execution.
- No inference.
- No SQL/qdrant writes.
- No direct rewrite of `00_global.dot` in this patch.


## Exact rule-test lock phrases

architecture DOT graphs, graph documentation, and some changelogs are not fresh enough.

## Exact rule-test lock phrases — 0173

architecture DOT graphs, graph documentation, and some changelogs are not fresh enough.

code surfaces that exist and pass tests.

rule tests and manifests.

planned 0162..0172 chain.

stale DOT files only as historical input.

Changelogs are useful but incomplete.

code plus passing tests wins.

stale changelog is then marked as a documentation gap.
