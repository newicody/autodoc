# ControlProxy operational plan — 0099 graph audit update

## Status after 0098

The ControlProxy route path now has enough runtime pieces to require a graph audit
before adding more mechanics.

Completed runtime line:

```text
0079 ControlProxy prepare/sizing + bus visibility
0080 mmap fixed-slot route
0081 active route materializer
0082 RouteNotifier eventfd/pipe
0083 route lease state
0084 tick_controlproxy()
0085 scheduler-facing prepare handshake
0086 scheduler request/reply adapter
0088 concrete scheduler handler
0089 write -> notify -> selector -> drain
0090 RouteMessage journal
0091-r2 route generation table g2/g3
0092 generation lifecycle cleanup
0093-r2 existing bus visualization read tap
0094 generation lock
0095 locked materializer
0096 explicit runtime placement
0097 graph alignment
0098 dispatch filter envelope
0099 architecture graph inventory and runtime overlay
```

## Corrected interpretation

The policy/zone mechanism is now described as dispatch filtering first:

```text
policy/zone dispatch filtering
not a separate ControlProxy security authority
```

The mechanism is security-inspired, but its role here is to decide and constrain
where work is dispatched.

## Graph integration rule

Every future runtime graph must answer four questions:

1. Which root graph node owns the zoom?
2. Which individual graph is being extended?
3. Is this a command path or an observation path?
4. Does the patch alter `Scheduler.run()` or only add a handler/use-case?

If a graph cannot answer those questions, it is isolated and must not be added as
an architectural authority.

## Scheduler.run() release rule

Do not modify `Scheduler.run()` yet.

A future patch may propose a Scheduler.run() change only after a concrete handler
shows that the current path cannot express the behavior:

```text
Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
```

Until that proof exists, the next coding work should compose around Dispatcher
and handlers.

## Proposed next steps

0100 should integrate `RouteDispatchFilterEnvelope` into the 0088 handler path
without changing Scheduler.run().

0101 should add route-zone policy records if the existing PolicyEngine contract
has a clean extension point.

0102 should add a graph consistency test that reads the graph registry and
ensures runtime graph files declare their root anchor.

0103 can then revisit whether ControlProxy deserves a package-level facade class
or remains a small set of cooperating classes under `src/runtime/`.
