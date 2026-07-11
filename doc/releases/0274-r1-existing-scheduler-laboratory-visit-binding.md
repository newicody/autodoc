# 0274-r1 — Existing Scheduler laboratory visit binding

This release activates the r3 deterministic fake laboratory through the one
existing Scheduler path.

The caller submits `LABORATORY_VISIT_REQUEST` to the already-running Scheduler.
The existing policy, queue, `Scheduler.run()`, Dispatcher and Handler return an
immutable receipt through `Request.reply`.

No new Scheduler, queue, EventBus or registry is introduced. 0274-r2 will
compose this live visit with the existing server-oriented deliberation and
synthesis contracts.
