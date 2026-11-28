# Route notification primitive

Status: 0082 implementation.

This phase adds a real notification primitive usable from Python without a
daemon and without adding a CLI.

## Problem

The mmap route from `0080-r2` can store frames, but a reader still needs a
cheap way to know that frames are available.

The notification primitive provides this sequence:

```text
writer writes RouteMessage frame to mmap route
writer calls notifier.notify(1)
reader/select loop sees notifier.fileno() readable
reader drains notifier counter
reader drains mmap route frames
```

## Implementation choice

Use existing kernel/Python/libc primitives from Python:

```text
preferred: Python os.eventfd
fallback: libc eventfd through ctypes
fallback: non-blocking pipe
```

No custom C extension is required.

## Why eventfd

`eventfd` is the clean Linux primitive for counter-style wakeups:

```text
one fd
counter semantics
selector-friendly
cheap wakeup
usable across processes later
```

The pipe fallback keeps tests and non-Linux development usable.

## API

```text
RouteNotifier.create(route_handle, backend="auto")
RouteNotifier.fileno()
RouteNotifier.notify(count=1)
RouteNotifier.wait_once(timeout=0.0)
RouteNotifier.drain()
RouteNotifier.close()
```

Helper functions:

```text
notify_after_write(notifier, written_count=1)
drain_ready_count(notifier)
eventfd_available()
```

## No daemon, no service

This phase intentionally does not add:

```text
daemon
service
OpenRC
ControlFS watcher
Scheduler call
lease issuing
lease handoff
VisPy renderer
```

## No CLI

This patch intentionally does not add a CLI.

The rule remains:

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Integration with mmap

The primitive is used around the mmap route, not inside its layout:

```text
MmapFixedSlotRoute.write_message(...)
RouteNotifier.notify(1)
RouteNotifier.wait_once(...)
RouteNotifier.drain()
MmapFixedSlotRoute.drain()
```

The notifier does not modify slot size and does not resize mmap routes.

## Next

The next phase should introduce route lease state transitions without adding a
daemon:

```text
not_leased -> leased -> active -> draining -> closed
```

A later ControlProxy pump/tick can call importable functions explicitly. It is
not a service and not a resident daemon.
