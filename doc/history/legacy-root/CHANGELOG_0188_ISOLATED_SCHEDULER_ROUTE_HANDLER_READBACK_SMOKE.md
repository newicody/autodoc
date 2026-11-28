# Changelog — 0188 Isolated Scheduler route handler readback smoke

## Added

- Isolated readback smoke for RouteProxy frames written by 0187.
- Verification that readback does not create new frame files.
- Optional `isolated_scheduler_route_handler_readback_smoke.jsonl` output.
- Tests/rules locking that handler execution, writer permits, frame writes,
  Scheduler.run, Scheduler/EventBus instantiation, ControlProxy frames, GitHub
  API, network, conversion, inference, SQL, Qdrant, and VisPy are untouched.

## Not changed

- No Scheduler.run modification.
- No route handler execution.
- No new RouteProxy frame write.
- No ControlProxy frame write.
