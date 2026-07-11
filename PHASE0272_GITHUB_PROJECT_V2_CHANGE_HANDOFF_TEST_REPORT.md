# Phase 0272-r6 test report — GitHub ProjectV2 change handoff

## Scope

- change set r4 to immutable handoff batch;
- reuse of the existing `SourceCandidate` contract;
- bounded candidate creation;
- local-only CLI;
- GitHub Actions operator configuration documentation;
- runtime and canonical graph updates.

## Review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing rules cover typed policies, immutable results, bounded work and IO boundaries
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
non_stdlib_dependency_added: false
```

## Expected validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

The patch construction workspace also runs the targeted r4/r5/r6 regression
suite and Graphviz syntax checks. Final counts are recorded in the patch README.

## Construction validation

```text
git diff --check: OK
compileall synthetic r4/r5/r6 workspace: OK
targeted r4/r5/r6 regression suite: 26 passed
runtime DOT syntax: OK
canonical DOT syntax: OK
network calls during tests: none
```

## Fresh archive verification

The generated archive was extracted over a detached synthetic r5 base, then its
`patch.diff` was checked and applied with Git. The same 26-test r4/r5/r6 suite,
compileall and both DOT parses passed again. The CLI executable mode remained
`100755`.
