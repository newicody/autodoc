# Authorized context-impact execution — 0287-r7-r8-r6

## Purpose

Apply an effect-free r8-r5 impact decision through existing execution and
observation boundaries without turning EventBus, ControlProxy or a laboratory
into an orchestration authority.

## Boundary map

```text
SQL context revision authority
        │
        ▼
r8-r5 ContextImpactPlan
(action_executed = false)
        │
        ▼
Scheduler policy authorization
+ exact plan SHA-256
+ expected task-state versions
        │
        ▼
existing Dispatcher/Event boundary
CONTEXT_IMPACT_EXECUTION
        │
        ▼
SchedulerContextImpactExecutionHandler
        │
        ├── Scheduler-owned task mutation port
        │     ├── rebind
        │     ├── checkpoint rebase
        │     ├── restart
        │     ├── fork
        │     └── stale-result marker
        │
        ├── EventBus observation
        │     └── CONTEXT_IMPACT_EXECUTION_RESULT
        │
        ├── Scheduler-issued laboratory notification
        │     └── LABORATORY_CONTEXT_UPDATE
        │
        └── existing route adapter, only when explicitly requested
              └── missipy.scheduler.route_adapter_request.v1
```

## Authority rules

| Surface | Responsibility |
|---|---|
| SQL context authority | Stores accepted semantic revisions and provenance |
| r8-r5 policy | Computes an effect-free impact proposal |
| Scheduler policy | Authorizes the exact plan digest |
| Scheduler mutation port | Applies idempotent task-state changes |
| EventBus | Observes execution and distributes facts |
| Laboratory notification | Carries the Scheduler decision to affected labs |
| ControlProxy route adapter | Applies only an authorized transport transition |

## Reproducibility

A task result keeps the revision it actually consumed. If a later revision
makes it obsolete, the result is marked stale against that revision rather than
rewritten. Restart and fork create derived execution identities, preserving the
old execution and context lineage.

## Idempotence

A mutation reference is bound to the digest of its complete immutable payload.
A replay of the same payload returns the stored receipt. Reusing the reference
with another payload is an idempotency collision and fails closed.

## Transport rule

Context change and route change are independent. No route adapter call occurs
unless the Scheduler-owned execution target explicitly declares
`route_transition_required=true`, supplies a route identifier and targets an
action eligible for transport transition.
