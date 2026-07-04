# Fake runtime replace semantics

Status: corrective phase after 0074.

## Problem

The file-backed fake runtime originally replaced these surfaces:

```text
data.index.jsonl
event.bus.jsonl
context.bus.jsonl
```

but appended to route files:

```text
routes/<route_id>/messages.jsonl
```

That made repeated end-to-end runs non-deterministic.

A second run could produce:

```text
route_message_count = 6
record_count = 10
```

instead of the expected baby-fork counts:

```text
route_message_count = 3
record_count = 7
```

## Fix

`write_projection_to_fake_runtime` now replaces route files by default.

Direct `FakeLocalRouteTransport.send` still keeps append semantics for tests or future queue-like behavior.

## CLI behavior

`tools/write_baby_fork_fake_runtime.py` now replaces routes by default.

Use this only when append behavior is explicitly wanted:

```bash
--append-routes
```

## Non-goals

This phase does not add:

```text
real shared memory
real semaphores
ring buffer
RouteProxy daemon
Scheduler wiring
ControlFS mutation
NetworkBridge
HardwareBridge
cluster dispatch
```
