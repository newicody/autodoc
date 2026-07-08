# Changelog 0233 — Data-surface EventBus supervisor sources

## Added

- Added canonical data-surface supervision event helpers to the existing passive
  bus supervisor module.
- Added observed cell kinds for GitHub artifacts, SourceCandidate, SQL, Qdrant,
  rehydration, and pushback.
- Added tests and rules locking the observation-only boundary.

## Not added

- No new EventBus.
- No GitHub/SQL/Qdrant mutation.
- No rehydration/pushback execution.
- No Scheduler.run() usage.
