# Changelog — 0187 Isolated Scheduler route handler smoke

## Added

- First controlled isolated handler smoke using existing
  `handle_scheduler_route_command`.
- Runtime policy construction rooted in explicit `isolated_runtime_root`.
- Verification that frame paths remain under the isolated root.
- Optional `isolated_scheduler_route_handler_smoke.jsonl` output.
- Tests/rules locking that Scheduler.run, Scheduler/EventBus instantiation,
  ControlProxy frames, GitHub API, network, conversion, inference, SQL, Qdrant,
  and VisPy are untouched.

## Not changed

- No Scheduler.run modification.
- No production route write.
- No ControlProxy frame write.
