# Changelog — 0163 GitHub external artifact existing builders

0163 refactors the 0162 GitHub external artifact smoke to use existing builders
instead of parallel JSON-only packets.

## Changed

- `tools/run_github_external_artifact_smoke.py` now builds:
  - `GitHubProjectArtifact`
  - `GitHubSourceCandidate`
  - `ContextExplorationPlan`
  - `LLMSpecialistResult`
  - `GitHubProjectScenarioPacket`
  - passive context graph + DOT
  - `GitHubPublicationReviewPacket`
- `performed_actions` replaces ambiguous `runtime_actions no_*` output.

## Added

- 0163 tests for existing builder reuse
- 0163 code rule
- 0163 architecture document
- 0163 runtime DOT
- 0163 manifest and phase report

## Boundary

No runtime Python under `src/` is modified. No SQL/Qdrant/GitHub/network/
Scheduler/LLM/OpenVINO execution is introduced.
