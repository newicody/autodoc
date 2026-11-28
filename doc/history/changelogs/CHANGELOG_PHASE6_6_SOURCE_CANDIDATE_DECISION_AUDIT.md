# Phase 6.6 — SourceCandidate Decision Audit / Report

## Added

- Optional `SourceCandidateDecisionAuditPolicy` on decision commands.
- Stable JSON audit record for local operator decisions.
- Atomic audit write helper using stdlib-only filesystem IO.
- `audit_path` in `SourceCandidateDecisionResult` JSON/text output.
- CLI flags `--audit-file` and `--audit-without-candidates`.
- Unit, CLI and rule tests for the audit path.
- Architecture DOT for the decision audit flow.

## Scope

This phase records a local audit report after an explicit operator decision. The
authoritative state remains the local SourceCandidate store. The audit file is a
readable local artifact for review, traceability and future projection.

No network backend, project board, vector store or model runtime is introduced.

## Code rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: Phase 6.6 extends the existing decision live path with an optional local audit artifact.
live_path_status: green
live_path_uses_real_backend: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
