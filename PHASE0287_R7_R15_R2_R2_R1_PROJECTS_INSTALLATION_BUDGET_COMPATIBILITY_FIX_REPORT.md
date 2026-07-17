# Phase 0287-r7-r15-r2-r2-r1 — Projects installation budget compatibility fix

## Objective

Repair the cumulative `newicody/projects` installation guide after the
`0287-r7-r15-r2-r2` readiness patch exposed seven rule failures.

All failures were documentation compatibility failures:

- `INSTALLATION.md` exceeded the locked 380-line budget;
- the first literal `AUTODOC_COPILOT_ADVISORY_ENABLED=true` appeared before the
  locked safe-default marker;
- historical digest placeholders required by older cumulative rules had been
  removed instead of retained as explicitly invalid examples.

No readiness contract, GitHub transport, Scheduler, SQL, OpenVINO or Qdrant
behavior is changed.

## Resolution

The guide is rewritten as a concise cumulative runbook while preserving:

- bundle copy and update commands;
- safe Copilot-disabled installation order;
- local token setup;
- real ProjectV2 preview/digest/execution sequence;
- exact ProjectV2 and Actions readiness audit;
- short imported-run preview path;
- historical version and compatibility markers;
- links to the detailed Copilot runbooks.

The executable sequence remains:

```text
preview
→ extract .plan_digest
→ reject an empty digest
→ execute with --confirm-plan-digest "$PLAN_DIGEST"
```

The historical strings:

```text
--confirm-plan-digest '<PLAN_DIGEST>'
--confirm-plan-digest ''
```

are retained exactly once, after a heading that states they must not be
executed. The r15-r2-r2 rule is migrated to verify this placement instead of
forbidding their textual presence globally.

## Validation targets

```text
installation_line_count: 375
locked_budget: less than 380
safe_digest_command_present: true
legacy_digest_examples_executable: false
copilot_false_precedes_true: true
readiness_command_preserved: true
historical_markers_preserved: true
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: documentation compatibility only; existing rules remain authoritative
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

## Application boundary

This patch is intentionally based on the working tree where
`0287-r7-r15-r2-r2-projects-views-actions-readiness-repair` has already been
applied but failed its rule suite. Applying this corrective patch with
`--allow-dirty` allows the patch queue to rerun the rules and commit both units
together.
