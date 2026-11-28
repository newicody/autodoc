# Changelog — 0287 r16-r4-r2

## Added

- Pure strict selection contract for fetched `ready_runs`.
- Deterministic durable raw member-path resolution.
- Bounded local one-shot Copilot v2 Issue comment publisher.
- Local completion state written only after verified readback.
- Preview and execute reports with explicit remote-mutation boundaries.
- Architecture graph, rule, report, manifest, and rule tests.

## Reused

- Existing GitHub Actions artifact scan/fetch path.
- Existing Copilot advisory v2 publication preview builder.
- Existing controlled and idempotent Issue-comment publisher.

## Preserved

- Projects workflow `issues: read` boundary.
- Request authority and advisory non-authority.
- No SQL/Qdrant/Scheduler/laboratory work.
