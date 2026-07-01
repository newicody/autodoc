# Phase 5.14 — SourceCandidate local contract

This archive adds the local `SourceCandidate` contract.

## Purpose

Phase 5.14 introduces the local business object that will later connect the local
context loop to storage, reports and GitHub projection:

```text
raw local input / artifact-dir / future GitHub projection
-> SourceCandidateInput
-> SourceCandidate
-> SourceCandidateDecision
-> immutable status transition
```

No persistent storage is introduced in this phase.

## Files

```text
README.md
MANIFEST_CHANGED_FILES.md
PHASE5_14_TEST_REPORT.md
doc/SOURCE_CANDIDATE_CONTRACT.md
doc/CHANGELOG_PHASE5_14_SOURCE_CANDIDATE_CONTRACT.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/context/37_local_context_loop_cli.dot
doc/docs/architecture/context/38_source_candidate_contract.dot
src/context/__init__.py
src/context/local_context_loop_cli.py
src/context/source_candidate.py
tests/context/test_source_candidate.py
```

## New contracts

```text
SourceCandidateOrigin
SourceCandidateInput
SourceCandidatePolicy
SourceCandidateDecision
SourceCandidate
SourceCandidateCreationResult
build_source_candidate()
apply_source_candidate_decision()
allowed_source_candidate_statuses()
allowed_source_candidate_decisions()
```

## GitHub namespace note

`SourceCandidatePolicy.default_repository` defaults to:

```text
newicody/autodoc
```

This is only serialized metadata for future projection. Phase 5.14 performs no
GitHub API call and uses no token.

## Included Phase 5.13 hygiene fix

`src/context/local_context_loop_cli.py` is included to collapse a duplicated
`_write_report` function header to a single definition.

## Boundaries

```text
no persistent storage
no SourceCandidate report writer yet
no GitHub API
no token
no network
no daemon
no live Scheduler
no Qdrant
no LLM
no OpenVINO call
```

## Dependencies

No non-stdlib Python dependency was added.

## Tests

```bash
tar -xzf /path/to/autodoc_phase5_14_source_candidate_contract.tar.gz

PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context/test_local_context_loop_cli.py
PYTHONPATH=src pytest -q tests/context/test_context_engine_contract_lock.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.14 adds immutable local SourceCandidate contracts and a small CLI hygiene fix; no new programming rule is required.
```
