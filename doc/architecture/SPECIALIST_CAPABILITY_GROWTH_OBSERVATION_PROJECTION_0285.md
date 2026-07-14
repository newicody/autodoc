# Specialist capability growth observation projection — 0285-r7

## Decision

The r6 selection result is converted into immutable facts and published through the
existing EventBus. PassiveSupervisor derives a read model from the already-emitted
event. Neither observer can authorize, select, dispatch or persist anything.

```text
r2 proposal + evidence
        ↓
r3 portable revision lineage
        ↓
r4 operator decision
        ↓
r5 SQL-authoritative append-only history
        ↓
r6 Scheduler selection
        ↓
SPECIALIST_REVISION_SELECTION_RESULT
        ↓
existing EventBus (observation only)
        ↓
r7 PassiveSupervisor read model
        ↓
existing Cell Lens bridge / future r8 smoke
```

## Correlation

Every fact carries:

- `specialist_ref`;
- `revision_ref`;
- `proposal_ref`;
- `decision_ref`;
- `history_entry_ref`;
- `sql_ref`;
- `selection_ref`.

Digests cover the proposal, revision, history snapshot, history entry, Scheduler
policy, selection and complete observation projection.

## Event boundary

r7 reuses `EventType.SPECIALIST_REVISION_SELECTION_RESULT`, which r6 reserved for
passive projection. The event destination is `observability`; its metadata declares
`observation_only=True` and `command=False`.

The EventBus port contains only `publish(Event)`. It cannot dispatch a handler or
reply to a request.

## PassiveSupervisor boundary

The read model accepts only the reserved result event and canonical observation
facts. It exposes explicit false capabilities for revision authorization, Scheduler
selection, laboratory dispatch, SQL writes and Qdrant writes.

## Installation review

No change is required in the cumulative `newicody/projects` installation guide.
r7 has no GitHub workflow, form, variable, secret, field or deployment effect.
