# 0129 operational note — RouteProxy flow control

0129 keeps ControlProxy/RouteProxy as data-plane infrastructure.  It is allowed to act quickly on `/dev/shm` route zones, but it does not become Scheduler, PolicyEngine, SQL authority, or specialist logic.

```text
Scheduler
-> command / priority / context generation
-> RouteProxy lease and writer permit
-> /dev/shm route zone
-> worker frame exchange
-> EventBus observation fact
-> SQL durable state
```

The RouteProxy registry snapshot is a runtime mirror.  It may be distributed as observation facts for statistics and VisPy, but it is not durable state.
