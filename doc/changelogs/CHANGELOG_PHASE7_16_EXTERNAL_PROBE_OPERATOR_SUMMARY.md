# Changelog — Phase 7.16 External Probe Operator Summary

## Added

- `src/context/source_candidate_external_probe_operator_summary.py`
  - Reads external probe artifact indexes.
  - Produces ready/check/blocked operator summaries.
  - Writes JSON and renders text.

- `tools/source_candidate_external_probe_operator_summary_cli.py`
  - CLI for summary generation.

- Tests for context, CLI and rules.

## Not added

- No external call.
- No network.
- No Scheduler change.
- No DOT.
- No SVG.
