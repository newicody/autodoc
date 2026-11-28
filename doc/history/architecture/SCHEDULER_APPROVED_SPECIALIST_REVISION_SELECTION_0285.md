# Scheduler-approved specialist revision selection — 0285-r6

## Decision

The existing Scheduler path selects a specialist revision; no specialist, laboratory,
Copilot component or storage adapter may select itself.

```text
approved proposal/revision
        │
        ▼
SQL-authoritative append-only history (r5)
        │ durable result + sql_ref + snapshot digest
        ▼
EventType.SPECIALIST_REVISION_SELECTION
        │ Scheduler.emit → PolicyEngine → PriorityQueue
        ▼
existing Dispatcher
        │
        ▼
SchedulerApprovedSpecialistRevisionSelectionHandler
        │ pure policy validation
        ▼
immutable selection result
        ├── selected revision
        ├── operator decision ref
        ├── sql_ref
        ├── laboratory route
        └── execution boundary
```

## Required proof

The selector rejects a candidate unless:

1. the r5 adapter reports a durable write;
2. the supplied snapshot digest matches;
3. the entry is the latest history entry;
4. the embedded operator decision authorizes the revision;
5. the specialist descriptor is `ready`;
6. capability and input/output contracts match;
7. the target laboratory binding and visit mode match;
8. all required laboratory capabilities are available;
9. one preferred execution boundary is both available and allowed.

## Runtime boundary

The r6 handler is structurally compatible with the existing Dispatcher. Composition
registers it through the Dispatcher's existing `register()` method. The handler does
not import or instantiate `Scheduler`, `Registry`, SQL, Qdrant, OpenVINO, EventBus or
a laboratory provider.

`SPECIALIST_REVISION_SELECTION_RESULT` is reserved for the passive observation
projection in r7. The r6 handler returns the immutable result through the existing
cooperative request path; it does not publish a second event by itself.

## Side effects deliberately absent

- no SQL write;
- no Qdrant write;
- no laboratory dispatch or execution;
- no EventBus publication from business code;
- no GitHub or ProjectV2 mutation;
- no new Scheduler, registry or parallel orchestrator.

## Projects installation review

No workflow, form, field, variable, secret or deployment instruction changes in r6.
The cumulative Projects installation guide therefore remains unchanged.
