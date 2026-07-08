# 0220 Passive Bus Supervisor Cellular Snapshot Rule

The passive bus supervisor cellular snapshot is an observation-only surface.

## Required Boundary

The implementation:

- must use only the Python standard library
- must consume already-emitted event data
- must produce serializable snapshot data
- must keep `AUTHORITY_BOUNDARY["observation_only"]` true
- must keep runtime mutation flags false

The implementation must not call Scheduler.run.

The implementation must not:

- call GitHub APIs
- download artifacts
- mutate GitHub Projects or issues
- write SQL
- write Qdrant
- control RouteProxy
- control ControlProxy
- decide policy
- require VisPy

## VisPy

VisPy is a future view adapter only. Any future VisPy code must read a snapshot
or a passive event stream and render it. It must not become the owner of runtime
state, policy decisions, scheduler execution, SQL writes, Qdrant writes, GitHub
mutations, or proxy control.

## Placement

The 0220 module is deliberately placed as a contract/snapshot surface. It does
not replace the existing bus, scheduler, ControlProxy, RouteProxy, SHM, SQL,
Qdrant, GitHub, or policy modules.

## Traceability

Every future patch that emits events for this supervisor should include at least
one event reference usable by the snapshot:

- `policy_decision_id`
- `artifact_ref`
- `sql_ref`
- `qdrant_ref`
- `route_ref`
