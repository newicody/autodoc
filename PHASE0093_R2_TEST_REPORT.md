# Phase 0093-r2 test report

Scope: read existing event.bus/context.bus objects and project observable facts
to a stable VisPy/browser-ready snapshot.

## Commands to run

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_bus_visualization_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_bus_visualization_adapter_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Local patch-generation validation

```text
git apply --check: passed in patch worktree
python -m py_compile new files: passed
pytest targeted new tests: passed in minimal compatibility worktree
```

Full repository pytest must be run by apply_patch_queue.py in the developer
checkout.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0093-r2 adds an importable read adapter that attaches to an
existing EventBus and existing context snapshot source. It does not instantiate
EventBus, does not create a parallel bus, and does not add a CLI, daemon,
watcher, service, backend, Scheduler modification, Qdrant, LLM, OpenVINO,
network path, VisPy dependency, or browser runtime.
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
