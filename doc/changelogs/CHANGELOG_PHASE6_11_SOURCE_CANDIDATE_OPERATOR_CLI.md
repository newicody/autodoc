# Changelog — Phase 6.11 SourceCandidate Operator Command Surface

## Added

- Added `context.source_candidate_operator_cli` as a unified local operator command surface.
- Added subcommands delegating to existing SourceCandidate CLI adapters:
  - `intake`
  - `review`
  - `decide`
  - `review-audit`
  - `report`
  - `report-file`
  - `bundle`
- Added unit tests for dispatch, argument forwarding and command stability.
- Added rule tests ensuring the unified CLI remains an adapter only.
- Added DOT architecture documentation.

## Not added

- No new business capability.
- No new backend.
- No Scheduler modification.
- No network integration.
- No external API.
