# Phase 6.5 — SourceCandidate Decision Live Path

## Added

- `SourceCandidateDecisionCommand` and `SourceCandidateDecisionResult`.
- `run_source_candidate_decision()` local use-case.
- Scheduler result events `SOURCE_CANDIDATE_DECISION` and `SOURCE_CANDIDATE_DECISION_RESULT`.
- `SourceCandidateDecisionHandler`.
- `source_candidate_decision_cli.py` CLI adapter.
- Unit, live-path, CLI and rule tests.
- Architecture DOT for the decision path.

## Scope

This phase applies an explicit operator decision to an existing local
SourceCandidate and writes the updated candidate back through the real local JSON
store.

It does not contact GitHub, does not create issues, does not mutate a project
board, and does not introduce Qdrant, LLM or OpenVINO.

## Code rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Phase 6.5 reuses the existing Scheduler-first live path rule for a new SourceCandidate operation.
live_path_status: green
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
