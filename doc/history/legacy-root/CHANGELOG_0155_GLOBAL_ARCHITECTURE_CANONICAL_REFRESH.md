# Changelog — 0155 global architecture canonical refresh

## Purpose

Refresh the canonical architecture graph direction after the P1 runtime/vector/SQL evolution.

## Changes

- Fixed `doc/docs/architecture/runtime/116_github_publication_review.dot` by renaming the DOT keyword node `graph` to `context_graph`.
- Added a current P1 cluster to `doc/docs/architecture/00_global.dot`.
- Added the mandatory changelog policy for future phases.
- Added a retrospective changelog for phases 0129 to 0154.
- Added a runtime graph for this refresh step.

## Boundaries

- No Scheduler run loop change.
- No new runtime orchestrator.
- No new OpenVINO adapter.
- No new Qdrant adapter.
- No SQL worker.
- Historical DOT graphs are preserved.

## Next work

- Refresh runtime subgraphs family.
- Refresh context/inference/services graph families.
- Add a graph link integrity and DOT make gate.
- Close P1 with Qdrant recall to SQL readback.
