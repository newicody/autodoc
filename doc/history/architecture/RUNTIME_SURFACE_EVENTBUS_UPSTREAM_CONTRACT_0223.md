# 0223 — Runtime Surface EventBus Upstream Contract

## Decision

RouteProxy, ControlProxy, SHM, and Policy are upstream runtime/control surfaces
that may emit or expose canonical EventBus events for passive supervision.

The passive supervisor remains downstream-only. It observes these events through
the EventBus, updates CellularState in memory, and may expose an optional snapshot
or optional audit/replay output. It must not become a proxy controller, SHM owner,
policy authority, scheduler, worker, or transport layer.

Canonical path:

```text
Scheduler authority
RouteProxy / ControlProxy / SHM / Policy surfaces
  -> EventBus canonical event
  -> PassiveSupervisorSink
  -> CellularState in memory
  -> optional snapshot
  -> optional audit/replay
```

## Scope

This contract prepares the later functional integration by fixing the boundary
between fast runtime surfaces and passive supervision.

It covers events emitted by, or exposed on behalf of:

```text
RouteProxy
ControlProxy
SHM ring/status
Policy gate/decision
```

It does not implement the runtime connection yet. This phase is a written lock so
future code cannot drift into a parallel bridge, a status-file-first path, or a
control-plane mutation hidden behind supervision.

## Scheduler relation

The Scheduler remains the orchestration authority.

Runtime surfaces may reflect, route, block, drain, prioritize, or expose effects
of scheduler-driven activity, but passive supervision must not invoke or wrap
`Scheduler.run()` and must not dispatch handlers.

The intended authority relation is:

```text
Scheduler = orchestration authority
Policy = decision authority
Proxy/control plane = routing/control authority
SHM = fast exchange/status surface
EventBus = canonical observation transport
PassiveSupervisorSink = downstream observer
CellularState = projection of observed state
```

## EventBus relation

The EventBus is the normal observation transport.

Runtime surfaces should be observed by events carried on the EventBus. Status
files, JSONL replay, and snapshots are not the main runtime path.

Forbidden normal path:

```text
proxy status JSON -> supervisor
SHM dump -> supervisor
events.jsonl -> supervisor as primary transport
```

Canonical path:

```text
runtime surface -> EventBus -> PassiveSupervisorSink -> CellularState
```

Optional diagnostic path:

```text
PassiveSupervisorSink -> snapshot.json
PassiveSupervisorSink -> events.jsonl audit/replay
```

## RouteProxy observation

RouteProxy events may describe route-level visibility such as:

```text
route active
route draining
route blocked by authority
route lease visible
emitter lag
context changed
route health
```

The passive supervisor may display these states and references, but must not:

```text
create a route
modify a route
delete a route
claim a lease
release a lease
block an area
prioritize traffic
notify emitters as an authority
```

RouteProxy refs should remain references, for example:

```text
route_ref
cell_id
cell_kind
state
health
error
payload
```

## ControlProxy observation

ControlProxy events may describe control-plane visibility such as:

```text
control channel active
control channel degraded
lease observed
command rejected by authority
operator-visible status
proxy health
```

The passive supervisor must not become a control proxy.

It must not:

```text
send proxy commands
acknowledge commands as authority
change proxy routing
distribute registries as authority
write route/control state
```

## SHM observation

SHM events may describe ring/status visibility such as:

```text
ring active
ring backpressure
slot lag
reader lag
writer lag
context generation changed
blocked area visible
priority update visible
```

The passive supervisor must not own SHM.

It must not:

```text
open /dev/shm as a required runtime path
mmap raw SHM as an authority
write SHM
mutate slots
advance cursors
reset rings
block zones directly
```

A later implementation may reuse existing SHM/proxy observation surfaces if they
already expose safe events. If only raw SHM exists, a separate audited emitter must
translate it upstream into EventBus events; the passive supervisor still consumes
only the EventBus side.

## Policy observation

Policy events may describe decisions such as:

```text
allowed
blocked
deferred
requires review
denied by rule
gate open
gate closed
```

The passive supervisor may expose:

```text
policy_decision_id
state
health
reason
cell_id
cell_kind
error
payload
```

The passive supervisor must not decide policy. It may only reflect the decision
made by the existing policy authority.

## Cellular locality and movement

CellularState is a projection of observed state, not a storage owner.

Cells may be grouped by locality or runtime area, for example:

```text
scheduler locality
route proxy locality
control proxy locality
SHM locality
policy locality
GitHub/import locality
SQL/Qdrant locality
```

A cell may appear to move when a related data item, route, lease, source
candidate, artifact, or context is transmitted elsewhere. This movement is a
visual/projection concern: it records where the observed responsibility or data
reference is currently visible. It must not imply ownership transfer by the
supervisor.

## Minimal runtime-surface event fields

A supervisable runtime-surface EventBus event should expose enough information to
update CellularState without a heavy adapter:

```text
event_id
event_kind
emitted_at or observed_at
source
surface
cell_id
cell_kind
state
health optional
refs optional
payload optional
```

Runtime-surface refs include:

```text
route_ref
shm_ref
policy_decision_id
control_ref
scheduler_ref
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
pushback_ref
```

## Forbidden shortcuts

Future patches must not use this supervision path to introduce:

```text
new EventBus implementation
status-file-first bridge
mandatory events.jsonl transport
Scheduler.run wrapper
proxy controller
SHM raw reader as primary path
policy decision engine
SQL/Qdrant writer
GitHub mutation
VisPy runtime dependency
non-stdlib dependency
```

## Future implementation expectation

A later functional patch should update or extend the existing passive supervisor
surface instead of creating a parallel runtime.

Expected direction:

```text
existing EventBus event
  -> PassiveSupervisorSink.accept(event)
  -> existing CellularState/snapshot surface
```

Fallback/debug-only helpers may exist for replay, but must be named and documented
as replay or audit helpers, never as the canonical transport.
