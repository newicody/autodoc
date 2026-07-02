# Changelog — Phase 6.12 SourceCandidate Operator CLI Help Gate

## Added

- Added smoke tests for `python -m context.source_candidate_operator_cli --help`.
- Added subcommand help smoke coverage for the unified operator command surface.
- Added a rule test that keeps `source_candidate_operator_cli.py` adapter-only.
- Added DOT and release documentation for the help/preflight gate.

## Not added

- No new SourceCandidate business capability.
- No new Scheduler event.
- No network call.
- No GitHub API.
- No Qdrant, LLM, or OpenVINO path.
- No generated SVG artifact.
