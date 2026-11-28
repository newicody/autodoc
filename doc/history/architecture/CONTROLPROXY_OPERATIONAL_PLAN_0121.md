# Operational plan 0121 — GitHub Project scenario packet

0121 adds only a reference-only scenario contract. It does not change the route
runtime, ControlProxy, EventBus, Scheduler, Dispatcher, Queue, or PolicyEngine.

Operational order remains:

1. external fetch later produces a GitHub artifact;
2. artifact becomes a SQL source candidate;
3. caller persists it through SQLContextStore;
4. context exploration plans bounded trajectories;
5. specialist result proposes solution candidates;
6. publication packet can later be posted back by a GitHub adapter.

The local server remains the source of evolving context. GitHub is a workflow
surface and synchronization target, not the context authority.
