# PassiveSupervisor closed ResultFrame observation - 0266

## Intent

0266 builds a PassiveSupervisor read model from the 0265 EventBus observation
report:

```text
EventBus observation facts -> PassiveSupervisor read model
```

PassiveSupervisor observes only. EventBus facts remain facts, not commands.

## Boundary

0266 does not execute SQL, OpenVINO, or Qdrant. It does not subscribe to a live
bus, does not publish events, does not start services, does not modify
Scheduler.run, and does not introduce a RuntimeManager.

The supervisor output is a passive report containing accepted facts, rejected
facts, command-like fact count, and runtime violation count.

## Existing surfaces reused

```text
0265 closed_result_frame_eventbus_observation report
JSON reports under .var/reports
```

No new live supervisor daemon is introduced in this patch.

## Next step

0267 can prepare the GitHub scan-once handoff using the closed frame and passive
observation reports.
