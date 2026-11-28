# Fake local route transport

Status: P5-prep fake transport.

This phase validates the runtime message flow before real `/dev/shm`, semaphores or ring buffers exist.

## Goal

Simulate the future local runtime layout using JSONL files:

```text
<runtime_root>/
  data.index.jsonl
  event.bus.jsonl
  context.bus.jsonl
  routes/<route_id>/messages.jsonl
```

This lets tests exercise:

```text
DataHandle
EventBusMessage
ContextBusMessage
RouteMessage
```

without implementing the hot transport.

## What it proves

The fake transport proves that:

```text
baby_fork_report.json
-> runtime projection
-> fake data.index
-> fake event.bus
-> fake context.bus
-> fake routes/<route_id>
```

is coherent before any shared-memory implementation is introduced.

## What it does not prove

This phase does not prove performance, concurrency or kernel-level IPC.

It does not add:

```text
real shared memory
real semaphores
ring buffer
eventfd
futex
RouteProxy daemon
ControlFS watcher
Scheduler wiring
NetworkBridge
HardwareBridge
cluster dispatch
```

## Python API

```python
from runtime.fake_route_transport import (
    FakeLocalRouteTransport,
    write_projection_to_fake_runtime,
    load_fake_bus_messages,
)
```

## CLI

```bash
PYTHONPATH=src:. python tools/write_baby_fork_fake_runtime.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime
```

Expected files:

```text
.var/baby_fork_fake_runtime/data.index.jsonl
.var/baby_fork_fake_runtime/event.bus.jsonl
.var/baby_fork_fake_runtime/context.bus.jsonl
.var/baby_fork_fake_runtime/routes/baby_fork.retrieval/messages.jsonl
.var/baby_fork_fake_runtime/routes/baby_fork.variant_stub/messages.jsonl
.var/baby_fork_fake_runtime/routes/baby_fork.context_gate/messages.jsonl
```

## Next phase after this

The next phase should be one of:

```text
Recorder ingestion from fake runtime messages
optional baby-fork CLI flag to emit fake runtime projection
ControlFS desired route manifests for baby-fork routes
```

Still do not introduce real shm/semaphore transport until the fake flow is stable.
