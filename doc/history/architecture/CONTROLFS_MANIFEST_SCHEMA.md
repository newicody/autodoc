# ControlFS manifest schema

Status: Priority 1 executable schema.

This document defines the first manifest that the Scheduler can eventually write into ControlFS and that a future RouteProxy can validate before materializing shm routes.

This is still local-only. It does not implement real shm, semaphores, NetworkBridge, HardwareBridge or Scheduler wiring.

## ControlFS route manifest v1

Schema name:

```text
missipy.controlfs.route_manifest.v1
```

Path convention:

```text
/run/autodoc/controlfs/desired/routes/<route_id>/manifest.json
```

Example:

```json
{
  "schema": "missipy.controlfs.route_manifest.v1",
  "route_id": "baby_fork.retrieval",
  "task_id": "baby_fork_smoke",
  "zone": "workers",
  "scope": "context.read",
  "producer": "scheduler",
  "consumer": "retrieval_worker",
  "ttl_seconds": 30,
  "mode": "rw",
  "message_schema": "missipy.runtime.route_message.v1",
  "created_by": "scheduler",
  "created_at": "2026-07-04T20:00:00Z"
}
```

## Required fields

| Field | Meaning |
|---|---|
| `schema` | Must be `missipy.controlfs.route_manifest.v1`. |
| `route_id` | Logical route identifier. Not a path. |
| `task_id` | Task or project namespace. |
| `zone` | Security/runtime zone. |
| `scope` | Permission scope, preferably `subsystem.permission`. |
| `producer` | Component expected to produce messages. |
| `consumer` | Component expected to consume messages. |
| `ttl_seconds` | Route lease duration in seconds. |
| `mode` | One of `rw`, `ro`, `wo`, `control`. |
| `message_schema` | Expected route message schema. |
| `created_by` | Component writing the manifest, normally Scheduler. |
| `created_at` | Timestamp string. |

## Validation rules

Route IDs are logical names, not filesystem paths.

Valid examples:

```text
baby_fork.retrieval
baby_fork.variant_stub
baby_fork.context_gate
worker-01.events
```

Invalid examples:

```text
../escape
baby_fork/retrieval
 baby_fork.retrieval
baby_fork.retrieval 
```

Locked route ID rule:

```text
^[a-z0-9][a-z0-9_.-]{0,127}$
```

Other name fields allow letters, digits, underscore, dot, colon and dash, but never path traversal.

TTL rule:

```text
1 <= ttl_seconds <= 86400
```

Message schema rule:

```text
message_schema must start with missipy.
```

## Ownership rule

The intended ownership model remains:

```text
Scheduler writes desired/routes/<route_id>/manifest.json.
RouteProxy reads desired/ and writes active/status.
Workers never write desired/ or active/.
```

## Atomic write rule

When the Scheduler is later wired to ControlFS, it should not partially write manifests.

Recommended pattern:

```text
write manifest.json.tmp
fsync if needed
rename manifest.json.tmp -> manifest.json
```

## What this phase implements

This phase adds:

```text
runtime.controlfs_manifest.RouteManifest
runtime.controlfs_manifest.normalize_route_id
runtime.controlfs_manifest.route_manifest_path
runtime.controlfs_manifest.load_desired_route_manifest
tools/validate_controlfs_manifest.py
```

It does not add:

```text
real ControlFS daemon
real RouteProxy
real shm
semaphores
NetworkBridge
HardwareBridge
Scheduler refactor
```
