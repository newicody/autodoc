# ControlProxy operational plan — 0108 live path

0108 converts the 0101–0107 simplification locks into an executable scenario.
The path is deliberately small:

```text
Handler -> RouteRuntimeManager -> ControlFS + mmap/eventfd data plane
```

The Scheduler, PolicyEngine, PriorityQueue and Dispatcher boundaries remain as
locked by 0101–0107:

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
```

## Resulting confidence

The walking skeleton now proves that:

- a Scheduler-facing payload can pass through the thin handler adapter;
- RouteRuntimeManager can materialize g1;
- g2/g3 updates allocate a new generation instead of resizing g1;
- lifecycle active/draining/closed works through the manager;
- cleanup removes only a closed runtime generation;
- EventBus = observation only;
- Route mmap/eventfd = data plane, not EventBus;
- No ControlProxyBus, No RouteBus, No VisualizationBus.

## Next phases

0110 should be a cleanup/compatibility phase: mark older 0085/0086 helpers as
compatibility wrappers or route them explicitly through the thin handler/manager
path when safe.

0111 can then add a full Scheduler.run() integration test only if the handler
registration boundary is stable enough. Until then, 0108 remains the runtime live
path after Dispatcher selection.
