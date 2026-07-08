# 0220 Passive Bus Supervisor Cellular Snapshot

Patch 0220 resumes the passive bus supervisor direction without creating a
parallel runtime or a graphical authority. The added surface consumes events
that have already been emitted by scheduler, runtime, proxy, SHM, policy,
GitHub artifact, SQL, Qdrant, or pushback components and collapses them into a
deterministic cellular snapshot.

## Intent

The goal is to make the next implementation patches observable:

- GitHub Action artifact flow
- local read-only artifact fetch
- SourceCandidate import
- SQL/Qdrant promotion
- GitHub pushback
- runtime root stabilization
- bus/proxy/SHM consolidation
- policy execution gates

The supervisor is passive. It only reads event records supplied to it and writes
a snapshot artifact for human inspection.

## Boundary

The supervisor must remain:

- observation-only
- stdlib-only
- deterministic
- serializable
- safe to run in tests without graphics or network

The supervisor must not:

- call `Scheduler.run`
- call GitHub APIs
- download artifacts
- mutate GitHub Projects or issues
- write SQL
- write Qdrant
- control RouteProxy or ControlProxy
- decide policy
- require VisPy

VisPy remains a future optional view adapter only. It should consume the JSON
snapshot and never become the state owner.

## Event Shape

A passive event includes:

- `event_id`
- `event_kind`
- `cell_id`
- `cell_kind`
- `state`
- `observed_at`
- optional references: `route_ref`, `policy_decision_id`, `artifact_ref`,
  `sql_ref`, `qdrant_ref`, `shm_ref`
- optional `error`
- optional string payload

## Cell Kinds

Initial cell kinds are:

- `SCHEDULER`
- `EVENT_BUS`
- `GITHUB_ACTION`
- `GITHUB_ARTIFACT`
- `LOCAL_FETCHER`
- `SOURCE_CANDIDATE`
- `SQL_AUTHORITY`
- `QDRANT_PROJECTION`
- `REHYDRATE`
- `RESPONSE_ARTIFACT`
- `ROUTEPROXY`
- `CONTROLPROXY`
- `SHM_RING`
- `POLICY_GATE`
- `PUSHBACK`
- `UNKNOWN`

## Output

The snapshot contains:

- event count
- cell count
- blocked/failed/stale counts
- authority boundary flags
- latest cell state per `cell_id`
- cell references for traceability

This gives the following patches a stable observation target before live GitHub,
fetch, promotion, pushback, proxy, SHM, and policy work continues.

## 0221 Bus-Direct Supervisor Sink Update

Patch 0221 keeps the same passive supervisor surface and updates it instead of
creating a parallel bridge. The canonical runtime path is:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy
  -> EventBus -> PassiveSupervisorSink.accept(event)
  -> in-memory CellularState
  -> snapshot on demand
  -> optional audit/replay JSONL
```

The Scheduler remains the orchestration authority. It is an upstream EventBus
emitter, not a dependency controlled by the supervisor. The passive supervisor
must observe Scheduler events after they have reached the EventBus and must not
call `Scheduler.run`, dispatch handlers, or mutate runtime state.

`events.jsonl` is no longer a mandatory spine. It is an optional audit/replay
surface used for tests, diagnostics, and reproducibility. The live supervision
path is the in-memory sink fed by canonical EventBus events.

## 0222 Scheduler EventBus Supervisor Source Update

Patch 0222 keeps Scheduler central in the architecture without giving authority
to the passive supervisor. The canonical runtime path is:

```text
Scheduler
  -> canonical Scheduler EventBus event
  -> EventBus
  -> PassiveSupervisorSink
  -> in-memory CellularState
  -> optional snapshot/audit
```

The patch standardizes the Scheduler event shape with `cell_kind=SCHEDULER`, a
`scheduler:<ref>` source reference, optional handler payload, and the same refs
used by later RouteProxy, policy, SQL, Qdrant, SHM, GitHub, and rehydrate events.

The passive supervisor still does not import Scheduler, does not call
`Scheduler.run`, and does not dispatch handlers. It only observes events that are
already on the EventBus path.
