# 0100 — ControlProxy / micro-kernel direction audit

## Verdict

This patch records an architecture correction before adding more runtime code.
The repository has not fully deviated, but the graph became more advanced than the implementation.
The current code has two parallel ControlProxy lanes that are related but not yet unified:

1. `0081/0084/0085/0086/0088`: the Scheduler-facing active-route handshake lane.
2. `0091-r2/0092/0094/0095/0096`: the generation table, lifecycle, lock, and placement lane.

The graph must not imply that these lanes are already one single operational coordinator.
They must be shown as adjacent lanes under the same ControlProxy / ControlFS subsystem until a later patch introduces a real coordinator.

## Micro-kernel direction

The micro-kernel remains the owner of scheduling semantics:

```text
ComponentProxy -> Scheduler.emit() -> PolicyEngine.decide() -> PriorityQueue -> Scheduler.run() -> Dispatcher.dispatch() -> Handler
```

`Scheduler.run()` is still unchanged. The constraint must not be released only because ControlProxy is growing.
It can be reconsidered later only if a concrete handler integration exposes a real limitation of the loop.

## Correct role split

```text
Scheduler / PolicyEngine / PriorityQueue / Dispatcher
= component scheduling, policy decision, ordering, handler dispatch.

ControlProxy / ControlFS
= route capability subsystem behind a handler boundary.

RouteDispatchFilterEnvelope
= policy/zone dispatch filtering for already-decided work,
  not a security authority and not a second scheduler.
```

ControlProxy can reject incoherent input at its boundary, for example a missing route id, zone, policy decision id, or `authorized=True` marker.
That is a dispatch filter and consistency guard, not a new policy decision.

## The actual inconsistency

Some recent graph edges made the system look like this:

```text
Dispatcher -> RouteDispatchFilterEnvelope -> ControlProxy -> generation table -> lifecycle -> runtime
```

That is too compact and misleading.
It hides the fact that the current implementation still has a legacy active-route lane and a newer generation lane.
The correct graph must show:

```text
Dispatcher -> ControlProxySchedulerRouteRequestHandler

ControlProxySchedulerRouteRequestHandler -> legacy active-route handshake lane
ControlProxySchedulerRouteRequestHandler -> future unified route coordinator
future unified route coordinator -> generation table / lifecycle / lock / placement
```

Until the coordinator exists, the graph must mark the unification as planned, not current.

## Terminology correction

`ControlProxyZonePolicy` in the prepare module is a legacy name that can be misunderstood as a security-policy engine.
For the next code cleanup, the intended semantic name is closer to:

```text
RouteZoneSizingProfile
RouteDispatchSizingProfile
RouteRuntimeSizingProfile
```

The current object mostly contains sizing, timing, notify, overflow, and ring budget rules.
It should not be documented as a replacement for `PolicyEngine`.

## Next implementation decision

The next code patch should not add another parallel helper.
It should introduce one importable facade, for example:

```text
ControlProxyRouteCoordinator
```

Its role should be to select one route operation path behind the Dispatcher handler:

```text
reuse active route
create first generation
create next generation
activate candidate generation later
```

The coordinator must still be called from a handler and must still receive an already Scheduler/policy/zone-authorized request.
It must not become a scheduler, daemon, watcher, service, or policy engine.

## Graph rule

The graph must show ControlProxy as a bounded subsystem under the handler boundary.
It must not show ControlProxy as a sibling scheduler or as an alternate Scheduler.run path.
It must also not show event.bus or context.bus as command channels.
They remain observation/read surfaces.
