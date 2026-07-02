# Phase 6.12 code-rule alignment — SourceCandidate Operator CLI Help Gate

Phase 6.12 is a regression-gate phase. It stabilizes the operator command surface added in Phase 6.11.

## Alignment

- The unified CLI remains an adapter surface.
- Business logic remains in pure context modules and live Scheduler paths added in earlier phases.
- No Scheduler change is introduced.
- No external dependency is introduced.
- No network operation is introduced.
- No generated SVG is versioned.

## Required report block

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Existing Phase 6-r3 patch queue and CLI-adapter rules already cover this phase.
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
