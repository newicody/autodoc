# Changelog — Phase 7.12 External Probe Bundle CLI Dry-Run

## Added

- `tools/source_candidate_external_probe_bundle_cli.py`
  - Plans external probe bundle creation.
  - Writes nothing by default.
  - Creates the local bundle only with `--apply`.
  - Supports text and JSON output.

- `tests/tools/test_source_candidate_external_probe_bundle_cli.py`
  - Covers dry-run planning, apply mode and JSON output.

- `tests/rules/test_source_candidate_external_probe_bundle_cli_rule.py`
  - Ensures the CLI remains local-only and dry-run by default.

- `doc/maintenance/EXTERNAL_PROBE_BUNDLE_CLI.md`
  - Documents dry-run and apply usage.

## Not added

- No external service call.
- No network access.
- No remote mutation.
- No Scheduler change.
