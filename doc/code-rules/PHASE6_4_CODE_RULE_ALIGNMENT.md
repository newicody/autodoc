# Phase 6.4 — Code rule alignment

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Phase 6.4 applies the existing Phase 6-r3 patch queue hygiene rules by adding a read-only status/preflight command to the local development tool.
live_path_status: n/a
live_path_uses_real_backend: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

`apply_patch_queue.py` remains a development tool. It does not become a kernel component and does not contain Autodoc/MissiPy business logic.
