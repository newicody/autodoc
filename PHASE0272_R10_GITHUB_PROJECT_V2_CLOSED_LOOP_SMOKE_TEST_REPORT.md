# Phase 0272-r10 test report — ProjectV2 closed-loop smoke

## Scope

- r7 gate validation ;
- r8 SQL durable consumption and idempotent replay ;
- query/passsage E5 family compatibility ;
- r9 controlled Qdrant projection ;
- 0263 refs-only recall and SQL rehydrate ;
- dry-run closure ;
- real qdrant-client confinement to CLI ;
- laboratory boundary remains closed.

## Validation commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_closed_loop_smoke_0272.py \
  tests/tools/test_run_github_project_v2_source_candidate_closed_loop_smoke_0272.py
PYTHONPATH=src:. python -m pytest -q
```

## Construction validation

```text
compileall added Python files: required
focused deterministic tests: required
full repository suite: required on target checkout 0b338de
git diff --check: required
DOT syntax: checked when graphviz dot is available
network calls in focused tests: none
non_stdlib_dependency_added: false
```

- Added regression coverage for 0261 `query:` prefix and role propagation.
