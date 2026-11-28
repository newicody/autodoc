# Changelog — 0157 P1 single runner surface audit

0157 records the P1 runner decision.

## Decision

P1 closure must reuse `tools/run_local_artifact_vector_indexing_runner.py`.

The runner is the existing 0145 operator surface. It wraps the validated
Scheduler/RouteProxy/vector smoke path and must be extended or composed before
any new runner, worker, adapter or orchestrator is introduced.

## Evidence

The P1 rule audit from 0143 to 0152 passed.

Validated rule families:

- 0143 Scheduler vector indexing smoke
- 0144 Scheduler vector indexing result frame
- 0145 Local artifact vector indexing runner
- 0146 Artifact intake contract
- 0147 Dynamic artifact route refs
- 0148 SQL persistence handoff
- 0149 SQL context store persistence smoke
- 0150 SQL context store write surface audit
- 0151 SQL context store controlled write
- 0152 SQL context store configured DB path

## Changed

- Added P1 single runner surface audit documentation.
- Added 0157 code rule.
- Added 0157 runtime DOT.
- Added manifest and test report.

## Boundary

0157 is audit-only and does not modify runtime Python code.
