# Changelog — Phase 6.17 SourceCandidate Projection Handoff Dry-Run

## Added

- `src/context/source_candidate_projection_handoff_dry_run.py`
  - Builds a local handoff dry-run bundle from a projection bundle.
  - Copies the projection preview.
  - Writes a projection gate report.
  - Writes a handoff manifest.

- `tests/context/test_source_candidate_projection_handoff_dry_run.py`
  - Covers successful handoff dry-run creation, failing gate result and invalid policy.

- `tests/rules/test_source_candidate_projection_handoff_dry_run_rule.py`
  - Ensures the phase remains local-only and does not modify Scheduler.

- `doc/docs/architecture/context/57_source_candidate_projection_handoff_dry_run.dot`
  - Documents the local handoff dry-run flow.

## Not added

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
- No new CLI.
