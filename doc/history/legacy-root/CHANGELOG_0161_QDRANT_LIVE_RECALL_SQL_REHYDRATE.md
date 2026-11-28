# Changelog — 0161 Qdrant live recall SQL rehydrate

0161 adds a live recall smoke using the existing query embedding output and
Qdrant REST `/points/search`, then delegates SQL authority retrieval to 0159.

## Added

- `tools/run_qdrant_live_recall_sql_rehydrate_smoke.py`
- tests for query vector parsing, Qdrant search payloads, and dry-run plan
- 0161 code rule
- 0161 architecture document
- 0161 runtime DOT
- manifest and test report

## Boundary

No runtime Python under `src/` is modified.

No OpenVINO adapter, Qdrant adapter, SQL worker, Scheduler runner or query
orchestrator is introduced.
