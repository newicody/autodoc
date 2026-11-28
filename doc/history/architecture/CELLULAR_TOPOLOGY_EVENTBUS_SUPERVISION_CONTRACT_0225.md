# 0225 — Cellular Topology EventBus Supervision Contract

## Decision

The passive supervisor may expose a cellular topology, but that topology is a
projection of canonical EventBus events. It is not a new runtime, not a placement
engine, not a scheduler, and not a control plane.

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
  -> CellularTopology projection
  -> optional snapshot
  -> optional audit/replay
  -> optional VisPy view later
```

The topology describes where observable cells appear to be, how they are grouped,
and how a reference appears to move when data, context, route ownership, leases,
or handoff references are transmitted elsewhere.

Movement is observed. It is not caused by the supervisor.

## Relation to existing contracts

This contract extends the written passive-supervision direction locked by the
previous phases:

- the Scheduler remains the upstream orchestration authority;
- the EventBus remains the canonical transport;
- the passive supervisor remains downstream-only;
- `CellularState` remains an in-memory projection;
- `snapshot.json` remains optional;
- `events.jsonl` remains optional audit/replay, not the main path.

## Cell identity

A cell represents an observable unit in the supervision projection.

A cell should be identified by stable references when they exist.

Recommended identity fields:

```text
cell_id
cell_kind
surface
source
location_ref
route_ref
shm_ref
policy_decision_id
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
handoff_ref
pushback_ref
```

The supervisor must not invent authoritative identities for runtime objects. It
may derive display identities only for visualization or snapshot readability.

## Cell locality

Cells may be grouped by locality.

Locality is a descriptive grouping, not a scheduler placement decision.

Examples:

```text
scheduler node
route proxy zone
control proxy zone
SHM ring/slot group
policy gate
GitHub artifact flow
SourceCandidate intake area
SQL store area
Qdrant projection area
rehydration area
pushback area
```

A locality group may be represented by:

```text
location_ref
location_kind
parent_location_ref
zone_ref
node_ref
route_ref
shm_ref
```

The supervisor may show locality changes, but it must not allocate, pin, drain,
lock, or move runtime work.

## Cell movement

A cell may appear to move when an upstream event describes a handoff, transfer,
route change, lease change, context movement, or artifact/data promotion.

Examples:

```text
SourceCandidate imported from GitHub artifact
SourceCandidate promoted toward SQL/Qdrant projection
context rehydrated from sql_ref/qdrant_ref
route lease transferred
SHM ring slot advanced
policy gate blocked or released
pushback status emitted
```

The passive supervisor may update the projected cell locality after observing
such events.

It must not execute the movement.

## Movement event fields

A canonical EventBus event that describes projected movement should prefer common
fields instead of nested, incompatible payloads.

Recommended fields:

```text
event_id
event_kind
emitted_at
source
surface
cell_id
cell_kind
state
health
location_ref
previous_location_ref
next_location_ref
handoff_ref
route_ref
shm_ref
policy_decision_id
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
pushback_ref
error
payload
```

The supervisor should be tolerant of optional fields, but future emitters should
prefer these canonical names to avoid adapter sprawl.

## Authority boundary

The passive supervisor may:

```text
consume EventBus events
update CellularState
project cell locality
project observed movement
produce snapshot output
write optional audit/replay records
serve future read-only visualization
```

The passive supervisor must not:

```text
call Scheduler.run()
wrap Scheduler.run()
dispatch scheduler handlers
claim or release proxy leases
block or unblock proxy zones
write to SHM or mutate cursors/slots
read raw /dev/shm as a required path
decide policy
promote SourceCandidate records
write SQL
query/write Qdrant
mutate GitHub
send pushback
own VisPy runtime authority
```

## Scheduler relation

The Scheduler may emit events that describe orchestration locality and state.

The supervisor may show the Scheduler cell and related movements, but it does not
influence the Scheduler.

```text
Scheduler authority
  -> EventBus event
  -> PassiveSupervisorSink
  -> CellularTopology projection
```

## Proxy and SHM relation

RouteProxy, ControlProxy, and SHM events may describe locality, zone health,
leases, route changes, ring state, blocked areas, emitter lag, and context change.

The supervisor may project those states onto cells and groups.

The supervisor must not control RouteProxy, ControlProxy, or SHM.

## Policy relation

Policy may emit decisions such as allowed, blocked, deferred, escalated, or
released.

The supervisor may project the affected cell and the policy gate locality.

The supervisor must not decide policy.

## Data surface relation

GitHub artifact, SourceCandidate, SQL, Qdrant, rehydration, and pushback events
may describe data moving through the pipeline.

The supervisor may project this movement:

```text
GitHub artifact cell
  -> SourceCandidate cell
  -> SQL/Qdrant reference cells
  -> rehydration cell
  -> pushback cell
```

This is a visualization and diagnostic projection only. The data flow remains
owned by the existing runtime/data components.

## Snapshot shape

A topology-aware snapshot may include additional read-only fields:

```text
cells
locations
edges
movements
last_seen_at
last_event
authority_boundary
```

These fields are outputs. They must not become required runtime inputs.

## Design rule

If adding topology support requires a large adapter layer, a parallel bus, or a
status-file driven path, the EventBus event contract should be corrected first.

The preferred order is:

```text
clarify canonical EventBus fields
reuse existing emitters and sink state
project locality/movement downstream
keep snapshot/audit optional
add visualization later
```
