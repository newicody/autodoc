# Real implementation sequence from 0081

The local runtime now has enough pieces to start replacing smoke-only surfaces
with a real ControlProxy implementation.

## Current sequence

```text
0079-r2/r3
  ControlProxy sizing + prepare + bus

0080-r2
  file-backed mmap fixed-slot route

0081
  active route materializer
```

## Next real implementation steps

```text
0082 notification primitive
  eventfd abstraction with pipe fallback, no daemon and no CLI

0083 route lease state
  not_leased -> leased -> active -> draining -> closed
  file-backed lease.json plus active status update

0084 ControlProxy pump/tick
  implemented as tick_controlproxy()
  importable function, no service, no OpenRC, no resident daemon
  reads ControlFS desired/request state when explicitly called
  calls active route materializer
  publishes bus facts

0085 Scheduler handshake
  implemented as prepare_route_for_scheduler()
  calls ControlProxy pump/tick path
  acquires and activates route lease
  returns route_handle/lease to producer

0086 Scheduler route adapter
  implemented as handle_scheduler_route_request()
  wraps prepare_route_for_scheduler() behind an already-authorized request/reply boundary
  no Scheduler loop change

0087 VisPy adapter
  consumes context.bus/event.bus route state
```

## Boundary

The active route materializer is the seam between:

```text
declarative ControlFS
runtime mmap route
future Scheduler lease
future notification primitive
```
