# Baby-fork runtime message projection

Status: Priority 4 adapter.

This phase connects the baby-fork smoke project to the ControlFS / SHM Runtime vocabulary without changing the existing smoke pipeline.

## Goal

The baby-fork smoke project already proves:

```text
TaskContext v1
-> retrieval
-> VariantGeneratorStub
-> ContextGate
-> TaskContext v2
-> report/journal
```

This phase adds a projection layer that converts the existing baby-fork report into compact runtime schema messages:

```text
DataHandle
EventBusMessage
ContextBusMessage
RouteMessage
```

## Routes

Locked baby-fork route names:

```text
baby_fork.retrieval
baby_fork.variant_stub
baby_fork.context_gate
```

## Projected messages

The projection emits:

```text
data_handles:
  baby_fork_smoke:report

events:
  retrieval.completed
  variants.generated

contexts:
  context.versioned

routes:
  baby_fork.retrieval reply
  baby_fork.variant_stub event
  baby_fork.context_gate context_patch
```

## Why projection instead of direct rewrite?

This phase deliberately avoids modifying the current baby-fork core pipeline.

It is safer to keep the proven smoke project stable and add an adapter:

```text
baby_fork_report.json
-> runtime projection
-> event/context/route/data-handle messages
```

Later, the smoke project can emit those messages directly.

## CLI

```bash
PYTHONPATH=src:. python tools/export_baby_fork_runtime_projection.py \
  .var/baby_fork_smoke/baby_fork_report.json
```

## Non-goals

This phase does not add:

```text
real shared memory
semaphores
ring buffer
RouteProxy daemon
Scheduler wiring
ControlFS mutation
NetworkBridge
HardwareBridge
cluster dispatch
```

## Next phase after this

The next phase should decide whether to:

```text
1. wire baby-fork CLI to optionally export this projection
2. add a fake local route transport for tests
3. define recorder ingestion for runtime schema messages
```

No real shm/semaphore should be introduced until the message-level flow is stable.
