# Closed ResultFrame EventBus observation - 0265

## Intent

0265 attaches observation facts to the 0264 closed ResultFrame:

```text
closed ResultFrame -> EventBus observation facts
```

EventBus observation only. Events are facts, not commands.

## Boundary

0265 does not execute SQL, OpenVINO, or Qdrant. It does not start PostgreSQL,
OpenVINO, or Qdrant. It does not modify Scheduler.run and it does not introduce
a RuntimeManager.

The EventBus is used as an observation channel only. Events have no Request and
no reply path.

## Existing surfaces reused

```text
contracts.event.Event
contracts.event.EventType
kernel.event_bus.EventBus
```

The smoke path creates an in-memory EventBus, subscribes an observer queue,
publishes fact-only events, and drains the observer queue. It does not affect the
scheduler.

## Next step

0266 can attach PassiveSupervisor observation to these facts without making the
supervisor a command source.
