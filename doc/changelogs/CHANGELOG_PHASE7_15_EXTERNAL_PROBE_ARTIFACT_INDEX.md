# Changelog — Phase 7.15 External Probe Artifact Index

## Added

- `src/context/source_candidate_external_probe_artifact_index.py`
  - Scans local bundle directories.
  - Reads bundle manifests.
  - Produces a deterministic index.

- `tools/source_candidate_external_probe_artifact_index_cli.py`
  - CLI for writing and rendering the index.

- `tests/context/test_source_candidate_external_probe_artifact_index.py`
  - Covers discovery, filtering, JSON IO and rendering.

- `tests/tools/test_source_candidate_external_probe_artifact_index_cli.py`
  - Covers CLI text and JSON output.

- `tests/rules/test_source_candidate_external_probe_artifact_index_rule.py`
  - Ensures the indexer remains local-only and does not add DOT/SVG artifacts.

## Not added

- No external calls.
- No network.
- No Scheduler change.
- No DOT.
- No SVG.
