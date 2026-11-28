# ControlProxy graph root alignment — 0107

0107 aligns the architecture graphs after the simplification locks introduced
from 0101 to 0106. It answers one specific problem: recent runtime graphs were
useful, but they could be read as a second architecture next to the micro-kernel.
That reading is not allowed.

```text
ROOT_GRAPH: doc/docs/architecture/00_global.dot
root-attached runtime overlay
not an isolated graph
```

## Locked architecture line

The graph line remains:

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
```

The meaning of each block is locked as follows:

```text
Scheduler = loop, time, queue intake and cooperative execution
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution order
Dispatcher = EventType -> Handler only
Handler = thin adapter
Specialist branch owns business logic
RouteRuntimeManager = runtime data-plane boundary
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
```

## ControlProxy placement

ControlProxy is not a scheduler layer. In the graph it must appear under the
handler side of the Scheduler boundary:

```text
Scheduler.run()
-> Dispatcher
-> ControlProxy route handler
-> RouteRuntimeManager
-> ControlFS + mmap/eventfd data plane
```

ControlProxy does not manage global priorities. ControlProxy does not decide
policy/zone. ControlProxy does not own EventBus. ControlProxy does not create a
second bus.

The following concepts remain rejected:

```text
No ControlProxyBus
No RouteBus
No VisualizationBus
No scheduler-like ControlProxy coordinator
```

## Relation to existing individual graphs

The existing Scheduler graph family remains authoritative for the micro-kernel
boundary:

```text
doc/docs/architecture/scheduler/10_scheduler.dot
doc/docs/architecture/scheduler/11_dispatcher.dot
doc/docs/architecture/scheduler/12_event_bus.dot
doc/docs/architecture/scheduler/13_priority_queue.dot
doc/docs/architecture/scheduler/14_component_proxy.dot
```

The existing Context graph family remains authoritative for context ownership:

```text
TaskContext / ContextGate remain context authority
Qdrant remains projection/search only
```

0107 adds the runtime overlay under:

```text
doc/docs/architecture/runtime/97_controlproxy_root_alignment.dot
```

That overlay is a root-attached runtime overlay. It exists to show where
ControlProxy/RouteRuntimeManager lands relative to the existing root graph and
not to create a new graph root.

## Coverage of phases 0101 to 0107

```text
0101 -> 0102 -> 0103 -> 0104 -> 0105 -> 0106 -> 0107
```

Coverage summary:

```text
0101 locks the simplified responsibility model.
0102 audits existing paths and marks wrappers/runtime primitives.
0103 introduces RouteRuntimeManager as runtime boundary.
0104 makes the ControlProxy handler a thin adapter.
0105 locks priority/admission minimalism.
0106 locks EventBus versus data plane.
0107 attaches the runtime graph to the root graph structure.
```

## What 0107 deliberately does not do

0107 does not rewrite `00_global.dot` directly. That file is a long-lived phase
roadmap graph and is already dense. Directly editing it in this step would make
patch application fragile and would not by itself solve the ambiguity. Instead,
0107 adds a root-attached runtime overlay and rule tests that lock how it must be
read.

A later graph-rendering pass may merge overlays into generated SVG artifacts,
but that pass must still preserve the boundaries locked here.
