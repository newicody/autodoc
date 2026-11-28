# 0172 — Runtime activity graph / VisPy contract

## Decision

0172 defines the contract for using DOT/graph structures as an architectural
support for VisPy/browser activity views.

This patch is audit + contract only. It does not execute conversion, inference,
fetch, scheduling, or rendering.

The existing bus path remains authoritative for observation:

```text
event.bus/context.bus
-> bus_visualization_adapter
-> VisPy/browser view
```

DOT is a representation contract, not a command path. DOT can describe the
shape of activity, states, scores, successes, failures, and navigation modes,
but it must not become the runtime authority.

## Why DOT here

DOT is useful as a stable architectural representation because it can describe:

- nodes and edges
- groups/subgraphs
- titles and labels
- status transitions
- success/failure paths
- scoring/probability annotations
- population/life/death analogies for artifacts, tasks, routes, and files
- multiple view modes over the same facts

This makes DOT suitable as an intermediate support for VisPy/browser
visualization, while the actual facts still come from existing
`event.bus/context.bus` observation surfaces.

## View modes

The graph contract supports several view modes. A future renderer may select one
or more modes without changing the underlying facts:

- `architecture`: static architecture/layers/components
- `runtime`: live runtime activity
- `artifact`: GitHub artifact and dataset lifecycle
- `scheduler`: scheduler/route/handler activity
- `bus`: event.bus/context.bus observations
- `score`: success, failure, probability, confidence, retry counters
- `population`: born/alive/queued/running/succeeded/failed/dead/superseded
- `debug`: provenance, hashes, refs, exact schemas, source files

## Activity states

The locked state vocabulary for activity graph nodes is:

- `planned`
- `born`
- `discovered`
- `fetched`
- `synced`
- `validated`
- `queued`
- `running`
- `succeeded`
- `failed`
- `blocked`
- `dead`
- `superseded`
- `retrying`
- `stale`

These states are visualization states. They do not replace the existing project
status vocabulary and do not grant authority to the graph.

## Scoring fields

Future graph facts may carry optional scoring fields:

- `score`
- `confidence`
- `probability`
- `retry_count`
- `failure_count`
- `success_count`
- `age_seconds`
- `last_seen_at`
- `health`
- `population_count`

Scores are annotations for observation and operator understanding. They are not
policy decisions.

## Titles, navigation, and zoom

A future VisPy/browser adapter should support:

- global title
- subgraph/layer titles
- node titles
- edge labels
- zoom and pan
- selectable nodes
- inspectable metadata
- filters by layer/status/schema/source
- collapse/expand of subgraphs
- mode switching over the same underlying bus facts

These are UI/navigation requirements, not scheduler requirements.

## Existing surfaces to reuse

Future implementation must reuse or extend the existing surfaces:

- `src/runtime/bus_visualization_adapter.py`
- `src/runtime/shm_runtime_schema.py`
- `src/runtime/scheduler_route_adapter.py`
- `src/runtime/scheduler_route_handler_minimal.py`
- `src/runtime/scheduler_route_handshake.py`

No new bus should be introduced only to support graph display.

## Main graph update rule

The root architecture graph should be refreshed from the actual local state
before adding runtime activity graph edges.

The main DOT graph must be updated only with an exact local patch after auditing
the current file. Do not patch `doc/docs/architecture/00_global.dot` from stale
assumptions.

The intended global alignment is:

```text
GitHub Actions artifacts
-> configured server dataset
-> existing event.bus/context.bus facts
-> bus_visualization_adapter
-> DOT/VisPy/browser activity views
```

and:

```text
Scheduler/policy/zone
-> existing scheduler route adapter/handler/handshake
-> event.bus/context.bus facts
-> DOT/VisPy/browser activity views
```

## Non-goals

- No VisPy rendering implementation.
- No new EventBus.
- No parallel bus.
- No direct VisPy writer.
- No Scheduler.run() modification.
- No GitHub API call.
- No network.
- No remote mutation.
- No conversion execution.
- No inference.
- No SQL/qdrant write.


## Exact rule-test lock phrases

DOT can describe the shape of activity, states, scores, successes, failures, and navigation modes.

Do not patch `doc/docs/architecture/00_global.dot` from stale assumptions.
