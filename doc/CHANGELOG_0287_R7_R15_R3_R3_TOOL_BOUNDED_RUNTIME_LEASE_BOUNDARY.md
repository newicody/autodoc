# Changelog — 0287-r7-r15-r3-r3

## Added

- process-local `ImportedActionsRuntimeLease` contract;
- typed synchronous close hooks;
- exact close/replay receipts;
- reverse-order exact-once resource cleanup;
- runtime lease readback in imported-run preview output;
- focused lifecycle and architecture tests.

## Changed

- imported Actions runtime factories may return a lease or legacy direct ports;
- the r15 imported-run CLI closes tool-bounded resources after Scheduler
  shutdown and on failure paths.

## Unchanged

- no new Scheduler, manager, laboratory or backend;
- no PostgreSQL, Qdrant or OpenVINO construction in this patch;
- no remote mutation;
- existing direct-port factories remain supported.
