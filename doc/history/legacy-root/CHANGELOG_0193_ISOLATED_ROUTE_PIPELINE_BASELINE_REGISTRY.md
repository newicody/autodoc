# Changelog — 0193 Isolated route pipeline baseline registry

## Added

- Registry writer for accepted isolated route pipeline baselines.
- Compact JSONL entry with baseline ref and digest.
- Accepted baseline label: `isolated-route-pipeline-write-read-v1`.
- Tests/rules locking that no runtime import, handler call, RouteProxy runtime
  call, frame write, Scheduler modification, EventBus instantiation, GitHub API,
  network, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No runtime execution.
- No new runtime handler.
- No Scheduler.run modification.
- No production route write.
