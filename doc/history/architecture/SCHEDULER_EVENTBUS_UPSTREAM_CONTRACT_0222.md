# 0222 — Scheduler EventBus Upstream Contract

## Decision

The Scheduler remains the orchestration authority.

It is upstream of passive supervision and may emit or expose canonical runtime
state transitions on the EventBus. The passive supervisor is downstream-only and
must never become a scheduler, handler dispatcher, policy authority, or proxy
controller.

Canonical path:

```text
Scheduler authority
  -> EventBus canonical event
  -> PassiveSupervisorSink
  -> CellularState in memory
  -> optional snapshot
  -> optional audit/replay
```

## Scope

This patch is a written contract only.

It does not add runtime code, handlers, adapters, workers, bus implementations,
or Scheduler wiring. It exists to lock the architecture before a functional
integration patch is prepared.

## Scheduler authority boundary

The Scheduler may decide or coordinate:

```text
run lifecycle
handler sequencing
task dispatch ordering
policy gate entry
runtime transitions
retry/defer/cancel flow
backpressure response
context handoff intent
```

The passive supervisor may only observe:

```text
scheduler state
scheduler transition
handler selected
handler started
handler completed
handler failed
task queued
task dispatched
task deferred
task cancelled
policy gate entered
policy gate result observed
context handoff observed
```

The passive supervisor must not:

```text
call Scheduler.run()
wrap Scheduler.run()
replace Scheduler.run()
dispatch handlers
change task order
make policy decisions
control RouteProxy or ControlProxy
write SHM
write SQL
write Qdrant
mutate GitHub
```

## EventBus role

EventBus is the canonical transport for Scheduler observation.

The Scheduler side may publish an event directly, expose a hook that publishes an
event, or hand a scheduler-origin frame to an existing bus writer. The passive
supervisor consumes the bus downstream.

The default path must not be:

```text
Scheduler -> status.json -> supervisor
Scheduler -> events.jsonl -> supervisor
Scheduler -> custom bridge -> supervisor
```

Those file paths may exist only for audit, replay, smoke tests, or temporary dev
fallbacks.

## Minimal Scheduler-origin event

A supervisable Scheduler-origin event should carry:

```text
event_id
source = scheduler
surface = scheduler
event_kind
emitted_at or observed_at
cell_id
cell_kind = scheduler
state
health optional
refs optional
payload optional
```

Recommended scheduler states:

```text
idle
queued
running
waiting
blocked
deferred
success
failed
cancelled
draining
stopped
```

Recommended scheduler event kinds:

```text
scheduler_started
scheduler_stopped
scheduler_tick
scheduler_drain_started
scheduler_drain_finished
task_queued
task_dispatched
task_deferred
task_cancelled
handler_selected
handler_started
handler_completed
handler_failed
policy_gate_entered
policy_gate_observed
context_handoff_observed
```

## Refs

Scheduler-origin events may include references without dereferencing them in the
supervisor:

```text
task_ref
handler_ref
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

These refs are for visibility and later correlation. The passive supervisor must
not use them as authority to mutate external systems.

## Cellular projection

A Scheduler-origin event updates a scheduler cell or a child cell associated with
the observed task/handler/location.

Cells may be grouped by locality and may move when the data or task ownership is
transferred elsewhere. Movement is represented as observed state, not as a
supervisor decision.

Example:

```text
scheduler/main
scheduler/task/<task_ref>
scheduler/handler/<handler_ref>
scheduler/handoff/<handoff_ref>
```

## Relationship with policy, proxy, and SHM

Scheduler events may mention policy/proxy/SHM refs, but the detailed state of
those surfaces should be emitted by their own upstream components:

```text
Policy -> EventBus -> supervisor
RouteProxy -> EventBus -> supervisor
ControlProxy -> EventBus -> supervisor
SHM ring/status -> EventBus -> supervisor
```

The Scheduler can observe or coordinate those transitions, but the passive
supervisor must not merge their authority into the scheduler cell.

## Functional integration gate

A later functional patch may connect this contract to existing Scheduler and
EventBus surfaces only after auditing the repository for existing modules.

Before adding runtime code, the integration patch must verify:

```text
existing Scheduler surface reused
existing EventBus surface reused
no new bus introduced
no Scheduler.run() modification unless explicitly reviewed
PassiveSupervisorSink remains downstream-only
snapshot and audit remain optional
```

## Non-goals

```text
no new runtime loop
no new EventBus implementation
no new Scheduler adapter unless audit proves no reusable surface exists
no handler execution
no policy execution
no proxy or SHM mutation
no GitHub, SQL, or Qdrant mutation
no VisPy renderer
```
