# Phase 0272-r9 test report — ProjectV2 vector projection

## Scope

- durable r8 report validation;
- deterministic vector-space profile identity;
- E5 embedding compatibility checks;
- profile provenance in Qdrant payload;
- dry-run effect closure;
- real client confinement to CLI;
- SQL authority and future laboratory boundary.

## Validation commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_vector_projection_0272.py \
  tests/tools/test_project_github_project_v2_source_candidate_vector_0272.py
```

## Construction validation

```text
compileall added Python files: OK
git diff --check: OK
DOT syntax: checked when graphviz dot is available
network calls in focused tests: none
full repository suite: required on target checkout 54a1ff8
non_stdlib_dependency_added: false
```

## r9-r2 regression closure

The first target full-suite run reached `2553 passed, 1 skipped` before one
failure exposed an empty optional `model_path` metadata value from the injected
embedding producer.  The 0262 path correctly rejected it via
`OpenVINOEmbeddingVector`.  r9-r2 removes empty optional producer metadata before
projection and adds a focused regression test; the strict adapter contract is
unchanged.  The complete suite must be rerun on the target checkout.
