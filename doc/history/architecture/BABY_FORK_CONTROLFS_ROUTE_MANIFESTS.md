# Baby-fork ControlFS desired route manifests

Status: 0071 executable route manifests.

This phase gives the baby-fork smoke path real ControlFS desired manifests.

## Desired routes

```text
baby_fork.retrieval
baby_fork.variant_stub
baby_fork.context_gate
```

## Files written

```text
<controlfs_root>/
  desired/
    routes/
      baby_fork.retrieval/
        manifest.json
      baby_fork.variant_stub/
        manifest.json
      baby_fork.context_gate/
        manifest.json
```

## Ownership

The long-term owner is still the Scheduler.

In this phase, a tool writes the manifests to make the route layer testable before Scheduler wiring exists.

## CLI

```bash
PYTHONPATH=src:. python tools/write_baby_fork_controlfs_desired.py \
  .var/baby_fork_controlfs
```

## Non-goals

This phase does not add:

```text
active route creation
real shared memory
semaphores
RouteProxy daemon
Scheduler wiring
SecurityFS compiler
ControlFS watcher
NetworkBridge
HardwareBridge
cluster dispatch
```
