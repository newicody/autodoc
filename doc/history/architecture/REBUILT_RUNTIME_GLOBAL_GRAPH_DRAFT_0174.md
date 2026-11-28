# 0174 — Rebuilt runtime global graph draft

## Decision

0174 adds a rebuilt current-state graph draft and subgraph drafts. It does not
replace `doc/docs/architecture/00_global.dot`.

The goal is to build a fresher representation from:

- code surfaces that currently exist,
- tests/rules/manifests that guard those surfaces,
- the validated 0162..0173 chain,
- stale docs and changelogs only as historical context.

This is a current-state draft, not runtime authority.

## Why not rewrite 00_global.dot yet

`00_global.dot` is old but valuable. It carries accumulated roadmap and history.
A direct rewrite would risk deleting context that helps humans and AI agents.

0174 therefore creates a parallel draft:

```text
doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot
```

and explicit subgraphs under:

```text
doc/docs/architecture/runtime/0174_subgraphs/
```

A later patch may merge this into `00_global.dot` after review.

## Current-state global graph

The rebuilt draft represents the chain we are actually converging on:

```text
GitHub Project / issue / idea repo
-> GitHub Actions ticket artifact
-> Copilot preliminary opinion artifact
-> read-only artifact fetch
-> configured server dataset
-> raw/index/history/queue
-> scheduler-addressable work or bus-compatible observation facts
-> Scheduler / policy / zone
-> scheduler route handshake / adapter / handler
-> ControlProxy / RouteProxy runtime data plane when needed
-> OpenVINO / E5 / specialist work when scheduled
-> Qdrant projection/search
-> SQL durable store / rehydrate
-> review/publication artifact
-> GitHub validation surface
```

Observation is represented separately:

```text
runtime facts
-> event.bus/context.bus
-> bus_visualization_adapter
-> DOT activity graph support
-> VisPy/browser view
```

## Required subgraph drafts

0174 adds these draft subgraphs:

- `runtime-bus`
- `scheduler-route`
- `github-artifact-dataset`
- `vector-sql-qdrant`
- `controlproxy-routeproxy`
- `activity-graph-vispy`
- `docs-provenance`

They are designed as maintained subgraphs that can later feed the refreshed
global graph and the VisPy/browser view modes.

## Freshness status rules

Nodes and edges use status language from the active architecture vocabulary:

- `current`
- `validated`
- `partial`
- `planned`
- `historical`
- `superseded`
- `deprecated`
- `blocked`
- `stale-doc`

Do not use `abandoned` unless it is explicitly proven.

## Runtime authority rule

DOT and VisPy/browser are representation surfaces. They must not become command
paths.

Runtime authority remains with:

- Scheduler / policy / zone for orchestration and authorization,
- SQL/local dataset for durable authority where applicable,
- Qdrant only as projection/search,
- EventBus only as observation.

## Merge policy for later 00_global.dot refresh

A later merge into `00_global.dot` must:

- inspect the exact local `00_global.dot`,
- preserve useful historical roadmap notes,
- import reviewed current-state clusters from 0174,
- link to maintained subgraph files,
- mark stale areas explicitly,
- avoid deleting changelog holes silently,
- avoid claiming execution that does not exist,
- avoid turning DOT into runtime authority.

## Non-goals

- No runtime code.
- No VisPy renderer.
- No Scheduler modification.
- No new EventBus.
- No parallel bus.
- No direct VisPy writer.
- No GitHub API.
- No network.
- No conversion execution.
- No inference.
- No SQL/qdrant write.
- No direct `00_global.dot` rewrite.

## Exact rule-test lock phrases — 0174

does not replace `doc/docs/architecture/00_global.dot`

## Exact rule-test lock phrases — 0174

does not replace `doc/docs/architecture/00_global.dot`
