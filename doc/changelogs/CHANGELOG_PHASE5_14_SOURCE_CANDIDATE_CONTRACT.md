# Changelog — Phase 5.14 — SourceCandidate local contract

## Added

- `src/context/source_candidate.py`
  - `SourceCandidateOrigin`
  - `SourceCandidateInput`
  - `SourceCandidatePolicy`
  - `SourceCandidateDecision`
  - `SourceCandidate`
  - `SourceCandidateCreationResult`
  - `build_source_candidate()`
  - `apply_source_candidate_decision()`
  - allowed status/decision helpers
- `tests/context/test_source_candidate.py`
- `doc/SOURCE_CANDIDATE_CONTRACT.md`
- `doc/docs/architecture/context/38_source_candidate_contract.dot`

## Changed

- `src/context/__init__.py` exports the new SourceCandidate contracts.
- `doc/docs/architecture/context/37_local_context_loop_cli.dot` now points to
  SourceCandidate local contract as the next roadmap step.
- `doc/docs/architecture/00_global.dot` exposes SourceCandidate local contract in
  the Context Fabric layer.
- `src/context/local_context_loop_cli.py` includes a small 5.13 hygiene fix:
  the duplicated `_write_report` function header is collapsed to one definition.

## Boundaries

- No persistent storage.
- No report writer for SourceCandidate yet.
- No GitHub API.
- No token.
- No network.
- No daemon.
- No Scheduler mutation.
- No Qdrant.
- No LLM.
- No OpenVINO call.

## Dependencies

No non-stdlib Python dependency was added.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.14 adds immutable local SourceCandidate contracts and a small CLI hygiene fix; no new programming rule is required.
```
