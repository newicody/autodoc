# Phase 0287-r7-r15-r3-r16-r2 — Projects bundle managed manifest and drift audit

## Result

The `newicody/projects` installation bundle now contains a versioned ownership
manifest and a local read-only drift audit.

The manifest identifies every active Autodoc-managed source and destination,
known retired paths, and managed roots that may contain unknown extra files.
Only explicit retired paths can become safe deletion candidates.

The audit computes SHA-256 digests from current source and destination files.
It reports `identical`, `destination_missing`, `modified`, `source_missing`,
`obsolete_managed` and `retired_absent`.

Unknown extra files are operator-review evidence and are never deletion
candidates.

## CLI justification

A separate CLI is justified because `check_projects_bundle_readiness.py`
audits remote ProjectV2, workflow and Actions readiness, while this command
audits only local filesystem ownership and synchronization. Combining them
would couple remote transport readiness to local deployment hygiene.

The business logic remains in
`projects_bundle_manifest_contract.py`; the CLI only parses a typed command,
renders a stable result and chooses an exit status.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing typed CLI, immutable result, explicit policy and IO-boundary rules are sufficient
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: true
```
