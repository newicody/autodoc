# Phase 0275-r5-r1 test report — laboratory smoke signature fix

## Cause

The test used:

```python
FakeLaboratoryClosedLoopSmokeCommand("sc:x")
```

The current 0274 command requires the explicit `deliberation`, `handoff` and
`recall` contracts. Those contracts belong to the already-tested 0274
closed-loop path and should not be reconstructed by this wrapper unit test.

## Correction

The test injects an opaque typed command sentinel and mocks the asynchronous
0274 function boundary. It verifies forwarding and the resulting local GitHub
preview.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q   tests/context/test_github_dual_artifact_laboratory_smoke_0275.py   tests/rules/test_github_dual_artifact_laboratory_smoke_0275_r1_rule.py
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
runtime_modified: false
scheduler_created: false
scheduler_modified: false
external_dependencies_added: false
github_mutation_performed: false
test_only_fix: true
```
