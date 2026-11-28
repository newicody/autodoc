# Changelog — Phase 7.14 External Probe Bundle Runbook

## Added

- `doc/runbooks/SOURCE_CANDIDATE_EXTERNAL_PROBE_BUNDLE_RUNBOOK.md`
  - Documents dry-run before apply.
  - Documents expected local bundle files.
  - Documents safety flags and failure handling.
  - References the documentation SVG build policy workflow.

- `tests/docs/test_source_candidate_external_probe_bundle_runbook.py`
  - Verifies the runbook structure and key operator safeguards.

- `tests/rules/test_source_candidate_external_probe_bundle_runbook_rule.py`
  - Ensures the runbook stays local-only and does not add DOT/SVG artifacts.

## Not added

- No source module.
- No CLI change.
- No DOT.
- No SVG.
- No network.
- No Scheduler change.
