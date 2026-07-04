# Scheduler route handshake

Status: 0085 implementation.

This phase adds Scheduler-facing route handshake functions.

## Purpose

After `0084`, ControlProxy can materialize active routes with an explicit pump.
After `0083`, active routes can be leased.

`0085` connects those two steps for the Scheduler path:

```text
prepare_route_for_scheduler(...)
  -> tick_controlproxy(...)
  -> verify active route exists
  -> acquire route lease
  -> activate route lease
  -> publish handshake facts
  -> return route_handle + lease_id
```

## No service

No CLI.


This phase is not:

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
prepare_route_for_scheduler(controlfs_root, runtime_root, route_id)
```

## Idempotency

The handshake is idempotent for the same holder/scope:

```text
same holder + same scope + active lease -> return existing lease
```

It rejects conflicting ownership:

```text
different holder
different scope
closed lease
```

## Authority boundary

This module is Scheduler-facing but not the Scheduler itself.

It does not decide security policy. The caller must already be the authorized
Scheduler path. Security remains with:

```text
Scheduler
policy engine
zone/scope rules
```

## Bus facts

Event topic:

```text
scheduler.route.handshake.ready
```

Context topic:

```text
scheduler.route.lease.active
```

These are facts, not commands.

## What it refuses

```text
daemon
service
OpenRC
watcher
poll loop
Scheduler event loop implementation
security policy decision
zone/scope bypass
RouteMessage frame write
eventfd notification
route drain
live mmap resize
inter-process locks
VisPy renderer
CLI
```

## Next

`0086` can wire an actual existing Scheduler adapter/call boundary to this
handshake function, still without service.
