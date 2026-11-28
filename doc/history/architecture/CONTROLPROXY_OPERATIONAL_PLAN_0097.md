# ControlProxy operational plan update — 0097

0097 updates the plan after graph review.

## Structural rule for architecture graphs

ControlProxy route diagrams should be integrated into the root runtime graph as a
subgraph, not delivered as isolated phase-only graphs.

```text
Root graph, not an isolated phase graph.
```

Allowed structure:

```text
root Runtime ControlFS / SHM / Cluster Fabric graph
  cluster_policy_zone
  cluster_controlproxy_controlfs
  cluster_runtime_surfaces
  cluster_future_extensions
```

## Current trunk after 0097

```text
0088 Scheduler handler boundary
0089 producer write -> notify -> selector/drain
0090 RouteMessage journal
0091-r2 generation table: route_id -> current_generation
0092 candidate -> active -> draining -> closed cleanup
0093-r2 existing bus visualization adapter
0094 route generation file lock
0095 locked materializer
0096 explicit runtime placement: file root or real /dev/shm root
0097 integrated root graph + ControlProxy/ControlFS/zone alignment
```

## Next priorities

1. **0098 — route zone capability envelope**
   Implement a small importable guard that turns the existing Scheduler-facing
   request into a route capability envelope carrying `route_id`, `zone`,
   `policy_decision_id`, and authorized status. It must reject missing authority
   metadata but not decide policy.

2. **0099 — placement-aware route reply**
   Expose selected runtime placement in the Scheduler-facing route reply without
   modifying `Scheduler.run()`.

3. **0100 — file-backed to /dev/shm generation migration test**
   Validate `g1` file-backed and `g2` `/dev/shm`-backed without live resize.

4. **Only later — kernel loop change decision**
   Reopen `Scheduler.run()` only if Dispatcher + Handler cannot express the
   concrete behavior without hiding state. The default remains no loop change.

## ControlProxy module shape

ControlProxy/ControlFS should converge toward one bounded code subsystem made of
small classes/modules, not one mega-class:

```text
ControlProxyFacade
  ControlFSStore
  RouteRequestAdapter
  RouteGenerationTable
  RouteGenerationLock
  RouteGenerationMaterializer
  RouteRuntimePlacement
  RouteLifecycle
  RouteBusProjection
```

Dispatcher is still required. It is the kernel dispatch boundary; ControlProxy is
one handler target behind that boundary.
