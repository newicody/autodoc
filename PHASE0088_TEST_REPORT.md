# 0088 — Test report — ControlProxy Scheduler handler

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_scheduler_handler.py
PYTHONPATH=src:. pytest -q tests/rules
```

## Expected result

```text
status: green
```

## code_rule review block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0088 implements a concrete importable Scheduler/Dispatcher handler boundary and keeps Scheduler.run, PriorityQueue, Dispatcher, and Component contracts unchanged.
live_path_status: transition
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
```

## Local validation status

This patch is generated as a patch-queue artifact. The current execution
container does not contain `~/projet/git/autodoc`, so full local post-0087 tests
must be run by `apply_patch_queue.py` on the target repository.

The patch itself is syntax-compiled in isolation and contains only additive
runtime, test, and documentation files.
