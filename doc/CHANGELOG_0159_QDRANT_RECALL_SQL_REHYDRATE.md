# Changelog — 0159 Qdrant recall SQL rehydrate

0159 adds a conservative operator smoke for the recall side of P1.

## Added

- `tools/run_qdrant_recall_sql_rehydrate_smoke.py`
- tests for sql_ref extraction and dry-run plan
- 0159 code rule
- 0159 architecture document
- 0159 runtime DOT
- manifest and test report

## Decision

Qdrant recall returns pointers. SQL rehydrate retrieves authority records.

## Boundary

No runtime Python under `src/` is modified. No Qdrant adapter, SQL worker, SQL orchestrator, Scheduler runner or OpenVINO runner is introduced.
