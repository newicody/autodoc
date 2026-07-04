# ControlProxy pump/tick

Status: 0084 implementation.

This phase adds an explicit importable ControlProxy pump.

## Vocabulary

```text
ControlProxy = ControlFS declarative surface + RouteProxy materializer
```

## No service

`0084` is not a service.

It is not:

```text
daemon
service
OpenRC
resident process
watcher
poll loop
CLI
```

It is:

```text
tick_controlproxy(controlfs_root, runtime_root)
```

The Scheduler, a test, or a future orchestration loop can call this function
explicitly.

## What one tick does

```text
read ControlFS desired/active routes
build RouteProxy dry-run plan
materialize missing desired routes
write mmap route files
write ControlFS active route state
publish event.bus/context.bus facts
return structured result
```

## What one tick refuses

```text
live mmap resize
implicit update of active route
delete/drain cleanup
lease issuing
security policy decision
Scheduler call
```

Updates are skipped with reason:

```text
update requires next generation; live mmap resize is forbidden
```

Delete/drain is skipped with reason:

```text
delete/drain cleanup is deferred to lease/drain phase
```

## Bus facts

Events:

```text
controlproxy.pump.route_materialized
controlproxy.pump.route_skipped
controlproxy.pump.route_error
```

Context:

```text
controlproxy.pump.active_route
```

These are facts, not commands.

## Implementation path

This becomes the real non-daemon execution seam:

```text
Scheduler / test / caller
-> tick_controlproxy()
-> reconciler plan
-> active materializer
-> mmap route
-> active route status
-> bus facts
```

## No CLI

This patch intentionally does not add a CLI.

The rule remains:

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Next

`0085` can add Scheduler-facing handshake functions that call the pump and then
acquire route leases. Still no service.
