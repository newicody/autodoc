# ControlProxy operational plan — 0124

0124 keeps ControlProxy and route runtime unchanged.

The operational center is now the local deliberation cycle:

```text
GitHub artifact exchange
-> ServerOrientation
-> specialist preliminary opinions
-> refined specialist demands
-> deliberation rounds
-> local synthesis
-> final artifact envelope
```

ControlProxy remains data-plane infrastructure. It is not the authority for context, policy, specialist deliberation, bus statistics, or GitHub publication.

The bus is used as an observation surface. Specialist bus statistics feed passive supervision and VisPy, not GitHub.

No Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, or RouteRuntimeManager file is modified by 0124.
