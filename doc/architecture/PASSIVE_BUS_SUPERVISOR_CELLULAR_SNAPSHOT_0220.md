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
