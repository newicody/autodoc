# Changelog — Phase 7.11 External Probe Bundle

## Added

- `src/context/source_candidate_external_probe_bundle.py`
  - Copies operator review and read-only probe artifacts into one local bundle.
  - Writes a deterministic manifest.
  - Preserves `read_only`, `external_call_performed` and `probe_allowed` flags.

- `tests/context/test_source_candidate_external_probe_bundle.py`
  - Covers bundle creation, manifest paths, repository mismatch, schema mismatch and rendering.

- `tests/rules/test_source_candidate_external_probe_bundle_rule.py`
  - Ensures the bundle remains local-only and source-only for architecture docs.

- `doc/docs/architecture/context/66_source_candidate_external_probe_bundle.dot`
  - Documents the local bundle boundary.

## Not added

- No real external adapter.
- No external API call.
- No network.
- No remote mutation.
- No Scheduler change.
