# Changelog — Phase 7.17 External Probe Local Audit Trail

## Added

- `src/context/source_candidate_external_probe_local_audit_trail.py`
  - Builds local audit events from operator summaries.
  - Appends events to JSONL.
  - Builds and writes a compact audit report.

- `tools/source_candidate_external_probe_local_audit_trail_cli.py`
  - CLI for recording summaries into the local audit trail.

- Tests for context, CLI and rules.

## Not added

- No external call.
- No network.
- No Scheduler change.
- No DOT.
- No SVG.
