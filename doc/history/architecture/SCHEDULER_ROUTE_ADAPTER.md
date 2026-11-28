# Scheduler route adapter

Status: 0086 implementation.

This phase adds a minimal adapter for the existing Scheduler boundary.

## Purpose

`0085` introduced:

```text
prepare_route_for_scheduler(...)
```

`0086` wraps that into a typed request/reply adapter:

```text
SchedulerRouteRequest
-> handle_scheduler_route_request(...)
-> SchedulerRouteReply
```

## Security boundary

The adapter requires:

```text
authorized=True
policy_decision_id=<non-empty id>
```

It does not decide security policy.

The request must already come from the authorized Scheduler path.

Security remains with:

```text
Scheduler
PolicyEngine
zone/scope rules
```

## Flow

```text
SchedulerRouteRequest
-> verify authorized=True and policy_decision_id exists
-> prepare_route_for_scheduler(...)
-> SchedulerRouteReply
-> publish adapter facts to event.bus/context.bus
```

## No service

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

No CLI.

It is:

```text
handle_scheduler_route_request(controlfs_root, runtime_root, request)
```

## Existing Scheduler boundary

The module is an adapter for the existing Scheduler boundary. It deliberately
does not implement:

```text
Scheduler event loop
PriorityQueue
Dispatcher
PolicyEngine
```

## Bus facts

Event topic:

```text
scheduler.route.adapter.ready
```

Context topic:

```text
scheduler.route.adapter.reply
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
PolicyEngine call
security policy decision
zone/scope bypass
desired manifest generation
RouteMessage frame write
eventfd notification
route drain
live mmap resize
inter-process locks
VisPy renderer
CLI
```

## Next

`0087` can connect the adapter to a concrete Scheduler handler object without
changing the Scheduler loop.
