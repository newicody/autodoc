# Changelog — Phase 6.15 SourceCandidate Projection Gate

## Added

- `src/context/source_candidate_projection_gate.py`
  - Validates local projection bundles before any future external handoff.
  - Checks manifest schema, preview schema, item counts and optional audit requirements.
  - Renders a stable text summary.

- `tests/context/test_source_candidate_projection_gate.py`
  - Covers valid bundles, missing manifest, audit requirement and rendering.

- `tests/rules/test_source_candidate_projection_gate_rule.py`
  - Ensures the phase stays local-only and does not modify Scheduler.

- `doc/docs/architecture/context/55_source_candidate_projection_gate.dot`
  - Documents the projection gate flow.

## Not added

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
