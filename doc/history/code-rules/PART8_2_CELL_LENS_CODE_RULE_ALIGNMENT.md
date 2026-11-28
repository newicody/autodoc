# Part 8.2 Cell Lens Code Rule Alignment

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: This patch adds supplemental observation rules for the cell lens. It does not modify runtime paths, but it introduces new architectural guardrails that future patches must obey.

live_path_status: documentation only
live_path_uses_real_backend: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
vispy_added: false
```

The new rules are intentionally documented before implementation because
`missipy.cell.v1` must exist before any renderer or mobile surface consumes
cell data.
