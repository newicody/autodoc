# Changelog 0221 — Passive supervision EventBus contract

## Added

- Added the canonical written contract for passive supervision through EventBus.
- Added the 0221 code rule that locks the supervisor as downstream-only.
- Added a DOT diagram for Scheduler/proxy/SHM/policy/GitHub/SQL/Qdrant event flow into the passive supervisor.
- Added a rule test that checks the contract keeps Scheduler authority, EventBus as the main path, and audit/replay optional.

## Not changed

- No runtime code was changed.
- No Scheduler code was changed.
- No EventBus implementation was changed.
- No proxy, SHM, policy, SQL, Qdrant, GitHub, or VisPy behavior was changed.
