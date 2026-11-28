# Part 8.0 Code Rule Alignment

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Part 8.0 adds a Python orchestrator for Roadmap B using Aider as a patch-bundle author. It preserves apply_patch_queue.py as the authoritative application path, disables Aider auto-commits and requires operator approval for rules, dependencies, Scheduler/runtime paths and large retroactive changes.

live_path_status: operator tool
live_path_uses_real_backend: local CLI only
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

The orchestrator may call Aider locally. It does not add a runtime dependency to
the application path.
