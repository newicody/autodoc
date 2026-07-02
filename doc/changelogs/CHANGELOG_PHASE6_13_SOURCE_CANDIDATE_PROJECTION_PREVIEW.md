# Changelog — Phase 6.13 SourceCandidate Projection Preview

## Added

- `src/context/source_candidate_projection_preview.py`
  - Builds a local projection preview from an operator report payload.
  - Writes a stable JSON artifact atomically.
  - Keeps the preview local and side-effect bounded.

- `tests/context/test_source_candidate_projection_preview.py`
  - Covers terminal filtering, limit handling, JSON serialization and invalid payload handling.

- `tests/rules/test_source_candidate_projection_preview_rule.py`
  - Ensures the phase stays local and additive.

- `doc/docs/architecture/context/53_source_candidate_projection_preview.dot`
  - Documents the local preview flow.

## Not added

- No external API.
- No network call.
- No project tracker mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
