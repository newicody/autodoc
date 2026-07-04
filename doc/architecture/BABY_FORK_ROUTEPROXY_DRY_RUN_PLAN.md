# Baby-fork RouteProxy dry-run plan

Status: 0072 executable dry-run plan.

This phase applies the existing RouteProxy dry-run reconciler to the baby-fork desired manifests.

## Path

```text
write baby-fork desired manifests
-> run RouteProxy dry-run reconciler
-> expect create actions when active/routes is empty
```

## Expected first plan

When no active route exists yet, the expected plan is:

```text
create baby_fork.context_gate
create baby_fork.retrieval
create baby_fork.variant_stub
```

## CLI

```bash
PYTHONPATH=src:. python tools/baby_fork_routeproxy_plan.py \
  .var/baby_fork_controlfs
```

## What this proves

This proves that the ControlFS desired state and the RouteProxy dry-run reconciler agree on the baby-fork route vocabulary.

## What this does not do

It does not materialize routes.

It does not add:

```text
real shared memory
semaphores
RouteProxy daemon
Scheduler wiring
active route creation
ControlFS watcher
NetworkBridge
HardwareBridge
cluster dispatch
```
