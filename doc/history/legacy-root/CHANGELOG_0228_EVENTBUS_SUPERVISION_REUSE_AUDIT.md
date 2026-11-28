# Changelog — 0228 EventBus supervision reuse audit

## Added

- Added a read-only reuse audit tool for the EventBus passive supervision functional
  resumption gate.
- Added tests proving the audit detects EventBus, Scheduler, and passive supervisor
  surfaces without importing runtime modules.
- Added architecture/rule documentation requiring reuse before any new runtime sink.

## Guardrails

- The audit is read-only.
- It does not call `Scheduler.run()`.
- It does not create a new bus.
- It keeps `events.jsonl` and snapshot outputs optional.
- It keeps the supervisor downstream-only.

## Reason

This patch satisfies the functional resumption gate by making the next runtime patch
start with explicit reuse evidence instead of creating parallel infrastructure.
