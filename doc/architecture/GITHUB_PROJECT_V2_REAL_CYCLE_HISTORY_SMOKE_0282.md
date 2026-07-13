# ProjectV2 real cycle-history smoke — 0282-r8

## Purpose

Close the 0282 implementation series by composing the already-existing
contracts and adapter into one replayable smoke:

```text
r4 append-only history
→ r5 parent/sub-ticket plan
→ r6 theme/grouping plan
→ r7 operator-authorized adapter
```

The r8 context contract performs only the first three local composition steps.
The r8 CLI delegates preview or execution to the existing r7 adapter.

## Two-pass execution

```text
Pass 1 — preview, default
  history + issue snapshots + theme command
  → deterministic r5/r6 plans
  → smoke_digest
  → r7 preview
  → no remote mutation

Pass 2 — explicit execution
  same immutable inputs
  + operator decision approve
  + --execute
  + exact prior smoke_digest
  → r7 receives exact individual plan digests
  → controlled remote mutations
```

A changed history, issue snapshot, title, summary, theme command, decision or
source reference changes the digest and blocks the second pass.

## Artifacts

The CLI writes a deterministic directory keyed by the first 16 characters of
the smoke digest:

```text
parent_sub_ticket_plan.json
theme_grouping_plan.json
smoke_result.json
adapter_report.json
tool_report.json
```

Repeated previews preserve identical content and report files as unchanged.

## Honest partial execution

The r7 adapter may perform one operation before a later operation fails. The r8
tool propagates:

```text
github_mutation_performed
partial_execution
execution_error
operation_results
```

It never reports an atomic rollback that GitHub did not provide.

## Boundaries

```text
existing_r7_adapter_reused: true
preview_is_default: true
exact_smoke_digest_required_for_execution: true
new_scheduler_added: false
new_mutation_transport_added: false
view_grouping_automated: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
external_dependencies_added: false
```

The Scheduler remains the sole Autodoc orchestrator. The visual Project view
grouping remains an operator step.
