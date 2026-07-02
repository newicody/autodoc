# Changelog — Phase 7.1 External Projection Contract v1

## Added

- `src/context/source_candidate_external_projection_contract.py`
  - Builds a target-neutral external projection contract from a handoff dry-run bundle.
  - Records gate status, projection permission and blocked reasons.
  - Adds item-level safety flags.

- `tests/context/test_source_candidate_external_projection_contract.py`
  - Covers allowed contracts, blocked contracts, target override, safety flags and JSON IO.

- `tests/rules/test_source_candidate_external_projection_contract_rule.py`
  - Ensures the contract remains local-only, target-neutral and Scheduler-free.

- `doc/docs/architecture/context/59_source_candidate_external_projection_contract.dot`
  - Documents the target-neutral contract boundary.

## Not added

- No GitHub adapter.
- No external API.
- No network.
- No remote mutation.
- No Qdrant.
- No LLM/OpenVINO.
- No Scheduler change.
