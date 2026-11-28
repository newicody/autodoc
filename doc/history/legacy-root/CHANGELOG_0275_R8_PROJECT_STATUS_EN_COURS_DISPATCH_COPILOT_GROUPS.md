# Changelog — 0275-r8 Project Status En cours dispatch, Copilot and groups

## Added

- pure ProjectV2 `En cours` dispatch-selection contract;
- idempotent local dispatch state;
- controlled GitHub workflow-dispatch CLI;
- bounded snapshot/diff/dispatch once-runner reusing 0272;
- theme-row and parent-issue box Board guidance;
- installation and validation runbook;
- focused unit, tool and rule tests.

## Changed

- projects workflow uses the ephemeral `GITHUB_TOKEN` for Copilot;
- projects workflow grants only `copilot-requests: write` in addition to read
  permissions;
- local ProjectV2 example config points at `newicody/projects`;
- one-minute bounded scan command composes snapshot, diff and dispatch;
- existing r7 workflow rule accepts the scoped Copilot permission.

## Boundaries

- no Project or issue mutation;
- no Scheduler or `Scheduler.run()` modification;
- no daemon or OpenRC service;
- no SQL or Qdrant write;
- no non-stdlib runtime dependency.
