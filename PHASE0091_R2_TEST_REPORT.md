# Phase 0091-r2 test report

Scope: ControlProxy route generation table with deterministic g2/g3 allocation.

## Commands to run

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_generation_table.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_generation_table_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Local patch-generation validation

```text
git apply --check: passed in patch worktree
python -m py_compile new files: passed
```

Full repository pytest must be run by apply_patch_queue.py in the developer
checkout.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0091-r2 adds a small importable generation table. It preserves
Scheduler authority, does not add a CLI, daemon, watcher, service, network path,
backend, Qdrant, LLM or OpenVINO integration, and does not resize a live mmap
route.
live_path_status: green
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
