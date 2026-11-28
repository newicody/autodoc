# Changelog — 0275-r2 GitHub dual-artifact contract

## Added

- added strict immutable request, advisory and manifest records;
- added SHA-256 and correlation validation;
- made the advisory optional but never authoritative.

## Boundaries

- one existing Scheduler only;
- SQL remains durable authority;
- GitHub mutation remains closed unless this phase explicitly reaches the guarded adapter;
- no secret is serialized.
