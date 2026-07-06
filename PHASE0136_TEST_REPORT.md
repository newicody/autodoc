# PHASE0136_TEST_REPORT

```text
phase: 0136-vector_indexing_qdrant_existing_path
code_rule_review: done
code_rule_update_required: true
code_rule_reason: locks vector-indexing/Qdrant reuse before any bridge or handler production change.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

Validation to run on the complete repository:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/inference/test_vector_indexing_qdrant_existing_path_0136.py tests/rules/test_vector_indexing_qdrant_existing_path_0136_rule.py
PYTHONPATH=src:. pytest -q tests/inference tests/rules
```

The patch generator environment does not contain the full `src/inference` and `src/context` stack, so this phase is validated structurally and should be executed on the complete working tree.

## 0136-r1 note

0136-r1 relaxes one integration assertion: the existing collection registry may expose role-oriented contract/specialist collection names without the literal historical strings `contracts_e5_384` and `specialist_outputs_e5_384`. The test now verifies registry reuse and collection semantics without requiring one exact collection naming spell.
