# 0099 — Architecture graph inventory and alignment audit

## Purpose

This patch answers the architecture-graph review request directly.

The repository currently has two graph families that must not diverge:

1. `doc/docs/architecture/00_global.dot` is the historical root roadmap graph.
   It links to the scheduler, context, services, experts, validation, learning and
   observability individual graphs.
2. `doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH*.dot` and the
   recent ControlProxy runtime phase documents describe the ControlFS / mmap /
   SHM route path added by phases 0079 through 0098.

0099 does not treat the ControlProxy graph as an isolated island. It records it
as a runtime overlay subgraph attached to the existing global architecture map.

## Graph structure to respect

The structure to respect is:

```text
doc/docs/architecture/00_global.dot
  -> scheduler/10_scheduler.dot
  -> scheduler/dispatcher/...
  -> scheduler/event_bus/...
  -> scheduler/priority_queue/...
  -> scheduler/component_proxy/...
  -> context/20_context.dot
  -> context/21_collector.dot
  -> context/22_reducer.dot
  -> context/23_snapshot.dot
  -> context/36_local_context_loop_design.dot
  -> services/30_services.dot
  -> experts/40_experts.dot
  -> validation/50_validation.dot
  -> learning/60_learning.dot
  -> observability/70_observability.dot
  -> runtime/90_controlproxy_runtime_overlay.dot
```

The new `runtime/90_controlproxy_runtime_overlay.dot` is a subgraph of the root
architecture family. It is not a separate runtime authority and not a second
root graph.

## Review of important individual graphs

| Area | Existing graph family | 0099 finding | 0099 action |
| --- | --- | --- | --- |
| Scheduler loop | `scheduler/10_scheduler.dot` and scheduler subgraphs | Still the authority for `emit -> policy -> queue -> run -> dispatcher -> handler`. | Keep unchanged; add runtime overlay links back to Scheduler, Policy, Queue and Dispatcher. |
| Dispatcher | `scheduler/dispatcher/*` and root Dispatcher node | The ControlProxy path must remain a handler target, not a Scheduler shortcut. | Represent `Dispatcher -> ControlProxySchedulerRouteRequestHandler`. |
| Event bus | `scheduler/event_bus/*` and root EventBus node | EventBus is facts/observation only. 0093-r2 must read an existing bus, not create one. | Represent an existing event.bus read tap only. |
| Context | `context/20_context.dot` and local context loop graphs | TaskContext/ContextGate remain context authorities; Qdrant is projection/search. | Add TaskContext, ContextGate and Qdrant projection edge in the overlay. |
| Services | `services/30_services.dot` | Runtime route work is not a general service daemon. | Keep route runtime out of services; show it as ControlProxy/ControlFS runtime overlay. |
| Observability | `observability/70_observability.dot` | Recorder/journal must receive drained facts, not commands. | Represent `RouteMessageJournal -> Recorder/ZFS`. |
| ControlFS/SHM runtime | `doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH*.dot` | Recent phases were represented, but not reconciled with the root graph family. | Add the canonical overlay graph and this audit. |
| Future cluster/bridge | ADR-0062 and runtime fabric docs | NetworkBridge/HardwareBridge are future boundaries. | Keep them dotted/future only. |

## Missing pieces found and represented

0099 adds explicit graph coverage for the important pieces that were not visible
together in the root-level graph family:

- `ControlProxySchedulerRouteRequestHandler` from 0088.
- `RouteWriteNotifyDrain` from 0089.
- `RouteMessageJournal` from 0090.
- `RouteGenerationTable` with g2/g3 generation state from 0091-r2.
- `RouteGenerationLifecycle` from 0092.
- existing-bus visualization adapter from 0093-r2.
- `RouteGenerationLock` from 0094.
- locked materializer from 0095.
- runtime placement policy from 0096.
- ControlProxy graph alignment from 0097.
- `RouteDispatchFilterEnvelope` from 0098.
- the nuance that the policy/zone mechanism is mainly dispatch filtering, not
  the business objective of security.

## Scheduler.run() decision

Do not release the `Scheduler.run()` constraint yet.

The current architecture can still express the ControlProxy path as:

```text
Component.tick()
-> yield Event / Request
-> ComponentProxy
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher.dispatch()
-> ControlProxy handler
-> Request.reply
-> ComponentProxy
-> tick().asend(result)
```

The constraint can be reconsidered only if a concrete isolated handler proves
that `Dispatcher -> Handler` cannot express the runtime path without breaking
determinism, replayability, or the event/queue authority model.

## ControlProxy / ControlFS / dispatch filtering

The preferred wording is now:

```text
ControlProxy/ControlFS is a bounded runtime subsystem.
ControlFS is the Unix-state surface.
ControlProxy owns route/control code around ControlFS.
Dispatcher calls the ControlProxy handler.
Scheduler/policy/zone remain the dispatch authority.
ControlProxy enforces the dispatch envelope; it does not invent policy.
```

The mechanism has a security-inspired shape, but its operational purpose here is
dispatch filtering and zone routing.

## 0099 code-rule alignment

- No CLI.
- No daemon.
- No service.
- No OpenRC unit.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue modification.
- No Dispatcher modification.
- No Component.tick/yield/reply contract modification.
- No Qdrant dependency added.
- No LLM or OpenVINO path added.
- No generated SVG added.
- Documentation is not pretending that an isolated graph is integrated.
- The new graph is explicitly a root-attached runtime overlay.
