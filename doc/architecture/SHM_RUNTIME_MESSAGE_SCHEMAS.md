# SHM Runtime message schemas

Status: Priority 3 executable schemas.

This document defines the compact message structures for the local SHM Runtime.

This phase is schema-only. It does not implement real shared memory, semaphores, ring buffers, Scheduler wiring, RouteProxy daemon, NetworkBridge or HardwareBridge.

## Schemas

```text
missipy.shm.event_message.v1
missipy.shm.context_message.v1
missipy.shm.data_handle.v1
missipy.shm.route_message.v1
```

## Rule: compact messages only

The hot buses must carry compact messages.

Allowed on buses:

```text
route_id
message_id
event_id
context_id
context_version
topic
source
target
zone
payload_schema
compact payload
data_handles
```

Not allowed on buses:

```text
large PDFs
large embeddings
large blobs
network streams
video/audio payloads
full datasets
```

Heavy payloads must be referenced with `DataHandle`.

## DataHandle

Schema:

```text
missipy.shm.data_handle.v1
```

Example:

```json
{
  "schema": "missipy.shm.data_handle.v1",
  "handle_id": "evidence-set-001",
  "storage": "zfs",
  "uri": "zfs://fast_pool/autodoc/artifacts/evidence-set-001.json",
  "content_schema": "missipy.baby_fork.evidence_set.v1",
  "size_bytes": 4096,
  "hash": "sha256:abc123",
  "producer": "retrieval_worker",
  "zone": "workers",
  "created_at": "2026-07-04T20:00:00Z",
  "ttl_seconds": 3600
}
```

Storage values:

```text
memfd
shm
tmpfs
zfs
nvme
remote
hardware
```

`remote` and `hardware` are future-compatible values. They do not imply that NetworkBridge or HardwareBridge exists now.

## EventBusMessage

Schema:

```text
missipy.shm.event_message.v1
```

Example:

```json
{
  "schema": "missipy.shm.event_message.v1",
  "event_id": "evt-001",
  "topic": "retrieval.completed",
  "source": "retrieval_worker",
  "occurred_at": "2026-07-04T20:00:00Z",
  "zone": "workers",
  "payload_schema": "missipy.baby_fork.retrieval_completed.v1",
  "payload": {
    "route_id": "baby_fork.retrieval",
    "retrieved_count": 2
  }
}
```

## ContextBusMessage

Schema:

```text
missipy.shm.context_message.v1
```

Example:

```json
{
  "schema": "missipy.shm.context_message.v1",
  "context_id": "baby_fork_smoke",
  "context_version": 2,
  "topic": "context.versioned",
  "source": "context_gate",
  "occurred_at": "2026-07-04T20:00:00Z",
  "zone": "context",
  "payload_schema": "missipy.task_context.patch.v1",
  "payload": {
    "selected_variant_id": "variant-1"
  }
}
```

## RouteMessage

Schema:

```text
missipy.shm.route_message.v1
```

Example:

```json
{
  "schema": "missipy.shm.route_message.v1",
  "route_id": "baby_fork.retrieval",
  "message_id": "msg-001",
  "kind": "request",
  "source": "scheduler",
  "target": "retrieval_worker",
  "occurred_at": "2026-07-04T20:00:00Z",
  "payload_schema": "missipy.baby_fork.retrieval_request.v1",
  "payload": {
    "context_id": "baby_fork_smoke",
    "context_version": 1
  }
}
```

Route message kinds:

```text
request
reply
event
context_patch
data_handle
control
```

## Python API

```python
from runtime.shm_runtime_schema import (
    DataHandle,
    EventBusMessage,
    ContextBusMessage,
    RouteMessage,
    parse_runtime_json,
)
```

## CLI

```bash
PYTHONPATH=src:. python tools/validate_shm_runtime_message.py message.json
```

## Non-goals

This phase does not add:

```text
real shared memory
real semaphores
ring buffers
RouteProxy daemon
Scheduler wiring
NetworkBridge
HardwareBridge
cluster dispatch
```

## Next phase after this

The next phase should integrate route vocabulary into the baby-fork smoke project:

```text
route_id in baby-fork report
event messages for retrieval.completed and context.versioned
data handle placeholder for evidence set if payload grows
```
