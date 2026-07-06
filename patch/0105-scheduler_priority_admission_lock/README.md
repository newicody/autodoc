# 0105 — Scheduler priority/admission lock

This patch locks the simplified priority/admission architecture before any
further ControlProxy runtime wiring.

It is documentation and tests only.

It does not modify Scheduler.run(), Dispatcher, PriorityQueue, PolicyEngine,
EventBus, handlers, Component contracts, or ControlProxy runtime code.
