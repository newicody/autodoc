# ControlProxy sizing and prepare protocol

Status: 0079-r2, replacing rejected 0079 and folding in the useful part of 0080.

## Vocabulary

```text
ControlProxy = ControlFS declarative surface + RouteProxy materializer
```

ControlFS and RouteProxy are treated as one runtime control unit.

## Locked route flow

```text
Producer / Worker
  -> Scheduler:
     short prepare frame with required_frame_bytes

Scheduler
  -> validates policy/security
  -> intends desired route state

ControlProxy
  -> applies zone table
  -> chooses slot_size / slot_count / max_frame_bytes / notify
  -> prepares/reuses/requests route generation
  -> publishes ready/denied state to event.bus and context.bus

Scheduler
  -> sees route ready
  -> returns route lease / route_handle

Producer
  -> sends full RouteMessage frame to prepared route
```

## Why this replaces old 0079

The old 0079 split ControlFS sizing from the proxy too much.

The corrected model is:

```text
route sizing
route preparation
route state publication
ControlFS desired state
RouteProxy materialization plan
```

as one ControlProxy protocol.

## Request schema

```text
missipy.controlproxy.route_prepare_request.v1
```

Minimal fields:

```text
request_id
route_id
task_id
zone
scope
producer
consumer
required_frame_bytes
message_schema
payload_kind
ttl_seconds
requested_by
requested_at
```

The prepare request is a short pre-frame. It does not carry the full payload.

## Status schema

```text
missipy.controlproxy.route_prepare_status.v1
```

Actions:

```text
reuse_active
create_route_generation
create_next_generation
deny
```

## Bus visibility

ControlProxy publishes facts to:

```text
event.bus
context.bus
```

Topics:

```text
controlproxy.route.ready
controlproxy.route.denied
controlproxy.route.state
```

This makes route preparation visible to:

```text
Recorder
Cell Lens
VisPy
browser view
future admin UI
```

Bus messages are facts, not commands.

## Timing budgets

Per-zone policy can bound:

```text
max_prepare_ms
drain_timeout_ms
lease_switch_timeout_ms
max_slot_size
max_ring_bytes
default_slot_count
```

If budget is exceeded, the route is denied or deferred. The system must not
resize a live mmap ring.

## Semaphore role

The semaphore does not create SHM and does not size slots.

It only signals:

```text
items available
free slots available
```

Slot sizing belongs to ControlProxy route preparation.

## Non-goals

This phase does not add:

```text
real shared memory
mmap implementation
live mmap resize
semaphores
eventfd
futex
ControlProxy daemon
ControlFS watcher
Scheduler wiring
VisPy renderer
NetworkBridge
HardwareBridge
cluster dispatch
```

## Next phase

The next phase can implement a file-backed fixed-slot mmap route that consumes
the ControlProxy decision.
