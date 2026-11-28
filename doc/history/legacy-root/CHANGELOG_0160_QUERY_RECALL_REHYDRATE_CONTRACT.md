# Changelog — 0160 query recall rehydrate contract

0160 adds a conservative contract smoke for the user-query side of the recall
path.

## Added

- `tools/run_query_recall_rehydrate_contract_smoke.py`
- tests for query-role normalization and dry-run plan
- 0160 code rule
- 0160 architecture document
- 0160 runtime DOT
- manifest and test report

## Decision

A user query enters the recall path as E5 `query:` text. Qdrant recall returns
`sql_ref` pointers. SQL rehydrate is delegated to 0159.

## Boundary

No runtime Python under `src/` is modified.

No OpenVINO adapter, Qdrant adapter, SQL worker, Scheduler runner or query
orchestrator is introduced.
