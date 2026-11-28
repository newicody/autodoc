# Changelog — Phase 7.18 External Probe Local Replay

## Added

- `src/context/source_candidate_external_probe_local_replay.py`
  - Reads local JSONL audit events.
  - Produces replay reports.
  - Supports latest-event limits.

- `tools/source_candidate_external_probe_local_replay_cli.py`
  - CLI for local replay reports.

- Tests for context, CLI and rules.

## Not added

- No external call.
- No network.
- No Scheduler change.
- No DOT.
- No SVG.
