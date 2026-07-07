# Changelog — 0189 Isolated route pipeline smoke

## Added

- End-to-end isolated route pipeline smoke combining 0179, 0184, 0185, 0186,
  0187, and 0188.
- Consolidated `isolated_route_pipeline_smoke.json` report.
- Tests/rules locking that Scheduler.run, Scheduler/EventBus instantiation,
  ControlProxy frames, GitHub API, network, conversion, inference, SQL, Qdrant,
  and VisPy are untouched.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No production route write.
- No ControlProxy frame write.
