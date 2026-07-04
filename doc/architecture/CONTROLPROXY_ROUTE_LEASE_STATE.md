# ControlProxy route lease state

Status: 0083 implementation.

This phase adds route lease state on top of active routes.

## Vocabulary

```text
ControlProxy = ControlFS declarative surface + RouteProxy materializer
```

## Goal

After `0081`, a route can be materialized as active. The Scheduler still needs
a stable state record before it can hand the route to a producer.

`0083` introduces explicit route lease files:

```text
active/routes/<route_id>/lease.json
active/routes/<route_id>/status.json
```

## State machine

Allowed path:

```text
not_leased -> leased -> active -> draining -> closed
```

Allowed shortcut:

```text
leased -> closed
```

Rejected examples:

```text
not_leased -> active
active -> leased
closed -> active
```

## Lease schema

```text
missipy.controlproxy.route_lease.v1
```

Fields:

```text
lease_id
route_id
route_handle
task_id
holder
scope
state
acquired_at
ttl_seconds
updated_at
```

## Active status update

The active route status receives:

```text
lease_state
current_lease_id
current_lease_holder
current_lease_scope
current_lease_updated_at
previous_lease_state
```

When the lease reaches `closed`, active route status `state` is also set to:

```text
closed
```

## Authority boundary

This module records lease state. It does not grant security by itself.

Security and authorization remain with:

```text
Scheduler
policy engine
zone/scope rules
```

## No daemon, no service

The Scheduler can call these importable functions directly.

This phase intentionally does not add:

```text
daemon
service
OpenRC
ControlFS watcher
Scheduler call
security policy decision
mmap route creation
RouteMessage frame write
eventfd notification
live mmap resize
inter-process locks
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

## Next

`0084` should be a ControlProxy pump/tick, not a service:

```text
ControlProxy pump/tick
-> reads desired/active route state when called
-> materializes missing active routes
-> updates lease state when requested
-> publishes bus facts
```
