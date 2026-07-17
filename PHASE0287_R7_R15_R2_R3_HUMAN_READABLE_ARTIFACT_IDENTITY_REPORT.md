# Phase 0287-r7-r15-r2-r3 report

## Goal

Make artifact names self-explanatory without weakening technical identity.

## Result

The Issue title and number now contextualize the three GitHub Actions artifacts. The artifact kind and schema version remain explicit in the suffix. A JSON identity index records display titles, summaries, content sections, legacy names and immutable references.

## Compatibility

Old runs keep working through exact legacy names. New runs are selected through strict canonical suffixes. A run containing both legacy and new names for one kind fails closed as ambiguous.

## Code-rule audit

The patch composes existing producers and consumers. It adds no manager, scheduler, worker, bus, registry, backend or external dependency. The identity contract is pure stdlib and immutable.

## Next

`0287-r7-r15-r2-r4 — readable Copilot publication wiring` will use these identities in ProjectV2 and Issue publication readbacks.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing immutable-contract and IO-boundary rules cover readable identities
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: autodoc.human_readable_artifact_identity.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
