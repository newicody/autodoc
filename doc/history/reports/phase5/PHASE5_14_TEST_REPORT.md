# Phase 5.14 test report — SourceCandidate local contract

## Local verification performed in artifact build environment

```text
py_compile src/context/source_candidate.py: OK
py_compile src/context/local_context_loop_cli.py: OK
py_compile src/context/__init__.py: OK
standalone SourceCandidate creation/decision smoke test: OK
dot 00_global.dot: OK
dot 37_local_context_loop_cli.dot: OK
dot 38_source_candidate_contract.dot: OK
archive hygiene: no SVG, no __pycache__, no pyc, no patch script
```

Graphviz emitted the known warning:

```text
Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

This warning is non-blocking and already appeared in earlier phases.

## Suggested project tests

```bash
PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context/test_local_context_loop_cli.py
PYTHONPATH=src pytest -q tests/context/test_context_engine_contract_lock.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Dependency review

No non-stdlib Python dependency was added.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.14 adds immutable local SourceCandidate contracts and a small CLI hygiene fix; no new programming rule is required.
```
