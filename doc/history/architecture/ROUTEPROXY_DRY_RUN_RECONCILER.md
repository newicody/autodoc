# RouteProxy dry-run reconciler

Status: Priority 2 executable dry-run layer.

This document defines the first RouteProxy behavior without creating real shared memory or semaphores.

## Goal

The RouteProxy is passive.

It does not call the Scheduler. It does not decide security. It does not create routes in this phase.

It only compares:

```text
/run/autodoc/controlfs/desired/routes/*
/run/autodoc/controlfs/active/routes/*
```

and produces a dry-run plan.

## Actions

The reconciler returns these actions:

| Action | Meaning |
|---|---|
| `create` | desired route exists, active route is missing |
| `delete` | active route exists, desired route is missing |
| `update` | desired and active route manifests differ |
| `noop` | desired and active manifests match, only when requested |
| `error` | invalid directory name or invalid manifest |

## Directory contract

```text
/run/autodoc/controlfs/
  desired/
    routes/
      <route_id>/
        manifest.json

  active/
    routes/
      <route_id>/
        manifest.json
```

This phase only reads those directories.

## Non-goals

This phase does not add:

```text
real RouteProxy daemon
inotify watcher
real shm
semaphores
eventfd
futex
Scheduler wiring
NetworkBridge
HardwareBridge
cluster dispatch
```

## Python API

```python
from runtime.routeproxy_reconciler import build_routeproxy_plan, summarize_plan

plan = build_routeproxy_plan("/run/autodoc/controlfs")
summary = summarize_plan(plan)
```

## CLI

```bash
PYTHONPATH=src:. python tools/routeproxy_dry_run.py /run/autodoc/controlfs
PYTHONPATH=src:. python tools/routeproxy_dry_run.py /run/autodoc/controlfs --summary
```

## Relationship to phase 0063

Phase 0063 defined:

```text
missipy.controlfs.route_manifest.v1
runtime.controlfs_manifest.RouteManifest
tools/validate_controlfs_manifest.py
```

Phase 0064 consumes that schema and produces the future RouteProxy plan.

## Next phase after this

The next phase should define SHM Runtime message schemas:

```text
event.bus message schema
context.bus message schema
data.index / DataHandle schema
route message schema
```

Still before creating real shm/semaphore transport.
