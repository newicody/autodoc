# ControlProxy operational plan update — 0098

0098 updates the ControlProxy vocabulary after the graph review and the
clarification that the Scheduler-side security-shaped envelope is mainly used
for dispatch filtering.

## Terminology update

Preferred wording:

```text
policy/zone dispatch filtering
```

Avoid presenting the ControlProxy path as if it were the security authority. It
is not.

```text
ControlProxy does not decide security policy.
Scheduler/policy/zone remain the authority.
```

The envelope contains security-shaped metadata, but the operational use is route
selection, filtering, and coherent dispatch into ControlFS.

## Current trunk after 0098

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
0098 RouteDispatchFilterEnvelope for policy/zone dispatch filtering
```

## Next priorities

1. **0099 — wire dispatch filter envelope into ControlProxy Scheduler handler**
   The handler should call `require_route_dispatch_filter_envelope()` before the
   concrete route adapter. This must remain a boundary filter and must not make
   ControlProxy a policy decision engine.

2. **0100 — placement-aware route reply**
   Expose selected runtime placement in the Scheduler-facing route reply without
   modifying `Scheduler.run()`.

3. **0101 — file-backed to /dev/shm generation migration test**
   Validate `g1` file-backed and `g2` `/dev/shm`-backed without live resize.

4. **Only later — kernel loop change decision**
   Reopen `Scheduler.run()` only if Dispatcher + Handler cannot express the
   concrete behavior without hiding state.

## ControlProxy module shape

ControlProxy/ControlFS should still converge toward one bounded code subsystem
made of small classes/modules:

```text
ControlProxyFacade
  ControlFSStore
  RouteRequestAdapter
  RouteDispatchFilterEnvelope
  RouteGenerationTable
  RouteGenerationLock
  RouteGenerationMaterializer
  RouteRuntimePlacement
  RouteLifecycle
  RouteBusProjection
```

Dispatcher remains required. It is the kernel dispatch boundary; ControlProxy is
one handler target behind that boundary.

## Dispatcher boundary reminder

Dispatcher is the kernel dispatch boundary. ControlProxy is the selected route
handler target behind that boundary.
