# PHASE0095_TEST_REPORT

```text
phase: 0095-route_generation_locked_materializer
code_rule_review: done
code_rule_update_required: false
code_rule_reason: importable composition around 0094 lock and 0091-r2 materializer; no new rule required.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
```

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_locked_materializer.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_locked_materializer_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Local generation notes:

```text
- patch generated as add-only files;
- no Scheduler, Queue, Dispatcher or Component contract files are touched;
- no CLI/service/watcher is added;
- no live mmap resize is introduced.
```
