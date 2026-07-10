# Operational documentation consolidation — 0270

## Purpose

0270 is documentation-only. It consolidates the validated 0260-0269 prototype
into the existing canonical entrypoints and removes obsolete roadmap wording from
the current map. It adds no runtime, handler, adapter, launcher, manager or daemon.

## Reuse audit

The repository already has canonical surfaces:

- `README.md` for the operator entrypoint;
- `doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md` for current state;
- `doc/ARCHITECTURE_LAYERS.md` for layer history and boundaries;
- `doc/docs/architecture/00_global.dot` as the master graph.

0270 updates those files instead of creating a competing architecture index. The
new 0270 document records the consolidation decision and the operational roadmap.

## Canonical validated chain

```text
0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268 -> 0269
```

The chain means:

- SQL write/readback is real and authoritative;
- OpenVINO/E5 embedding is real and explicit;
- Qdrant remains projection/recall with `payload.sql_ref`;
- the 0269 Qdrant executor is still an explicit demonstration membrane;
- EventBus emits observation facts only;
- PassiveSupervisor consumes a read-only model only;
- GitHub handoff is local and forbids remote mutation;
- OpenRC readiness does not start services;
- the final 0269 report closes only with nine valid steps and all boundary checks.

## Architectural decisions locked by 0270

### Process ownership

PostgreSQL, Qdrant and OpenVINO-related processes are started by OpenRC, the OS or
an administrator. Scheduler may use their capabilities through explicit adapters,
but it does not own their lifecycle.

### Durable and recall ownership

SQL is the durable source of truth. Qdrant is a rebuildable projection and recall
surface. A recalled item is useful only through its `sql_ref` and SQL rehydration.

### Observation ownership

EventBus is not a command bus. PassiveSupervisor is not a controller. Their
current use is passive observation of immutable facts and closed frames.

### GitHub ownership

GitHub is a review/workflow/synchronization surface. The local machine remains
authoritative. A remote mutation path requires a separate explicit gate and may
not be inferred from the local scan-once handoff.

### Scheduler boundary

`Scheduler.run()` is unchanged. No service manager, runtime manager or hidden
backend selection is introduced.

## Operational roadmap after 0270

### Decision A — real Qdrant executor

First audit the existing projection adapter, recall tools and live smoke surfaces.
Prefer binding or extending them. Require an explicit policy decision, configured
endpoint/collection, `payload.sql_ref`, readback verification and a no-durable-
authority assertion.

### Decision B — real read-only GitHub scan

Introduce network access only through a read-only adapter with explicit repository
scope, bounded requests, no token logging and `remote_mutation_allowed=False`.
Validate this before designing any write operation.

### Decision C — remote GitHub mutation gate

Treat mutation as a distinct later capability. Require operator approval, a typed
mutation intention, dry-run output, idempotency evidence and an auditable result.
No background mutation loop is implied.

### Decision D — optional OpenRC wrapper

Add a real service wrapper only if the deployment needs one. It must live outside
Scheduler, start only the local Autodoc entrypoint it owns, and continue to leave
PostgreSQL/Qdrant/OpenVINO lifecycle to explicit OS configuration.

### Decision E — later expansion

Specialists, cluster distribution and hardware acceleration remain later work.
They must build on the stable SQL/recall contracts rather than bypass them.

## Status vocabulary

```text
validated: exercised by a successful smoke/readback
transition: contract exists but a demo or injected membrane remains
planned: documented future direction, not current authority
historical: retained for traceability, not the current extension point
```

At 0270, the end-to-end prototype is validated as a composition; the real Qdrant
executor and real GitHub network adapter remain transition/planned decisions.
