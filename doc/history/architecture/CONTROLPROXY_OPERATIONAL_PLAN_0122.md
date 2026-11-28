# Operational plan 0122 — Passive context graph export

0122 adds a read-only graph export step after the GitHub Project scenario
packet.  It does not change ControlProxy, route runtime, EventBus, Scheduler,
Dispatcher, Queue, or PolicyEngine.

Operational order remains:

1. GitHub artifact is imported by a future external adapter;
2. artifact becomes a SQL source candidate;
3. caller persists through SQLContextStore;
4. context exploration and specialists produce result packets;
5. passive graph export reads the packet and emits DOT text;
6. future UI or documentation can render that DOT output.

The graph exporter is intentionally passive.  It reads contracts only and does
not observe live events.
