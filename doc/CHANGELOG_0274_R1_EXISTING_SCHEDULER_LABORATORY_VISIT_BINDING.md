# Changelog — 0274-r1 existing Scheduler laboratory visit binding

## Added

- explicit laboratory visit request/result event types;
- immutable event builder for a bounded laboratory visit;
- existing-Dispatcher Handler for the r3 provider membrane;
- submission helper using an already-running `SchedulerContract`;
- immutable Scheduler visit receipt with negative ownership assertions;
- live test through the existing Scheduler, queue, policy, Dispatcher and
  EventBus observation copy;
- architecture, manifest, release and rule gates.

## Not added

- no LaboratoryScheduler or LaboratoryManager;
- no second queue, EventBus, registry or runtime manager;
- no `Scheduler.run()` modification;
- no network or external dependency;
- no SQL/Qdrant/GitHub/VisPy behavior change.
