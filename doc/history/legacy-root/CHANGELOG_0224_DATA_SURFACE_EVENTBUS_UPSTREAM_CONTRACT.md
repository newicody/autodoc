# Changelog — 0224 Data Surface EventBus Upstream Contract

## Added

- Documented data-surface supervision contract for GitHub artifact,
  SourceCandidate, SQL, Qdrant, rehydration, and pushback surfaces.
- Added code-rule forbidding passive-supervisor mutation of GitHub, SQL, Qdrant,
  SourceCandidate, rehydration, pushback, Scheduler, proxy, SHM, and policy.
- Added DOT architecture graph showing EventBus as canonical transport and
  snapshot/audit as optional outputs.
- Added rule test to keep the contract traceable.

## Not added

- No runtime code.
- No GitHub client.
- No SQL/Qdrant adapter.
- No SourceCandidate promotion code.
- No rehydration executor.
- No pushback sender.
- No EventBus implementation.
- No Scheduler changes.
