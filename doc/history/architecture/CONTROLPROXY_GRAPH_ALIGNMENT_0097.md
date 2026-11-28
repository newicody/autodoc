# 0097 — ControlProxy graph alignment and zone boundary

Status: architecture alignment patch.

0097 corrects the graph direction after the route runtime placement work. The
runtime placement graph must not live as an isolated phase diagram. It belongs
inside the root Runtime ControlFS / SHM / RouteProxy / Cluster Fabric graph as a
ControlProxy/ControlFS subgraph.

## Decision

```text
Root graph, not an isolated phase graph.
```

The route generation and runtime placement path is represented as a subgraph of
the global architecture:

```text
SecurityFS / policy / zones
-> Scheduler / PolicyEngine
-> PriorityQueue / Scheduler.run() / Dispatcher
-> ControlProxy route handler
-> ControlProxy/ControlFS route-control block
-> locked generation materializer
-> route@gN/ring.bin under file or /dev/shm placement
-> existing event.bus/context.bus facts
-> Recorder / ZFS Store
```

## ControlProxy / ControlFS boundary

ControlProxy and ControlFS should be treated as one bounded subsystem, but not as
one monolithic class. The useful shape is:

```text
ControlProxy subsystem
  ControlFS store/surface
  Route request adapter
  Route generation table
  Route generation lock
  Locked materializer
  Runtime placement policy
  Route lifecycle cleanup
  Bus visibility projection
```

ControlFS is the Unix filesystem state surface. ControlProxy is the code block
that owns the route-control behavior around that surface. The older RouteProxy
wording remains useful only as a sub-role: the passive materialization role
inside the ControlProxy subsystem.

## Security and zones

The wording must stay precise:

```text
ControlProxy enforces authorized route decisions but does not decide policy.
Scheduler/policy/zone remain the authority.
```

ControlProxy may reject an invalid request envelope, for example when a route
request is missing:

```text
authorized=True
policy_decision_id
zone
route_id
```

That rejection is a boundary guard, not a new security decision. The actual
decision remains upstream in Scheduler/policy/zone. Zone metadata travels with
the route decision as capability metadata and then constrains where ControlFS
state and route generations are recorded.

## Dispatcher is not redundant

Dispatcher and ControlProxy are not duplicates:

```text
Dispatcher selects and invokes the registered handler.
ControlProxy route handler performs the route-control behavior behind that handler.
```

So the correct line is:

```text
Scheduler.run() -> Dispatcher -> ControlProxy route handler -> ControlProxy/ControlFS
```

not:

```text
Scheduler.run() -> ControlProxy directly
```

## Scheduler.run() lock

The current lock remains in force:

```text
No Scheduler.run() modification.
```

The lock can be reopened only by an explicit loop-extension design. The minimum
criteria are:

1. a concrete handler exists and is tested;
2. Dispatcher can no longer express the required behavior without hiding state;
3. PolicyEngine and zone checks stay before execution;
4. a rule test names the Scheduler files allowed to change;
5. the patch explains why the change is kernel-loop work and not ControlProxy shortcut work.

Until those criteria are met, ControlProxy continues to integrate through a
handler boundary.

## What was missing from the graph

The graph must show these items together, otherwise the architecture is easy to
misread:

- SecurityFS / policy / zones before ControlProxy.
- Dispatcher before ControlProxy handler.
- ControlProxy/ControlFS as one bounded subsystem.
- Generation table and lock before materialization.
- Runtime placement as a policy inside ControlProxy, not inside Scheduler.
- g2/g3 route generations and No live mmap resize.
- Existing event.bus/context.bus as observation surfaces, not bus creation.
- Recorder and ZFS after facts, not on the hot route-write path.
- NetworkBridge and HardwareBridge as future extensions only.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: architecture graph alignment and naming discipline; no new programming technique is introduced.
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

## Boundaries kept

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher, or Component tick contract modification.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- EventBus/context bus are existing observation surfaces, not commands.
- No live mmap resize; g2/g3 generations remain the update path.
- Not /dev/shm-only.
- No NetworkBridge or HardwareBridge implementation.
- No Qdrant, LLM, or OpenVINO path.
