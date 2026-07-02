# Changelog — Phase 6.14 SourceCandidate Projection Bundle

## Added

- `src/context/source_candidate_projection_bundle.py`
  - Builds a local projection bundle from an operator report JSON file.
  - Writes `projection_preview.json` and `manifest.json`.
  - Keeps all effects local and atomic.

- `tests/context/test_source_candidate_projection_bundle.py`
  - Covers manifest writing, preview writing, terminal filtering and policy validation.

- `tests/rules/test_source_candidate_projection_bundle_rule.py`
  - Ensures no external backend or Scheduler mutation is introduced.

- `doc/docs/architecture/context/54_source_candidate_projection_bundle.dot`
  - Documents the local projection bundle flow.

## Not added

- No external API.
- No network.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
