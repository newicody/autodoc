# Phase 0287-r7-r15-r2-r2-r2 — Projects installation remaining compatibility markers fix

## Objective

Restore the six cumulative installation markers still required by the full
`tests/rules` suite after the r15-r2-r2-r1 line-budget correction.

The failures are limited to documentation compatibility:

- the exact `0287-r5-r2-r2` compatibility heading was missing;
- the historical `0281` publication adapter marker was missing;
- the `0284-r9` phase table row was missing;
- the historical specialists/laboratories live-path verifier marker was missing.

No readiness contract, workflow, ProjectV2 transport, runtime source, Scheduler,
SQL, OpenVINO or Qdrant behavior is changed.

## Resolution

The cumulative guide is changed by four effective lines only:

- one existing compatibility bullet becomes the exact locked heading;
- two historical tool markers are restored near the runbook links;
- one `0284-r9` row is restored in the historical table.

The guide remains below the locked budget:

```text
installation_line_count: 379
locked_budget: less than 380
```

All previously repaired invariants remain unchanged:

```text
real_digest_command: --confirm-plan-digest "$PLAN_DIGEST"
legacy_digest_examples: documented only under ne pas exécuter
copilot_safe_default_order: false before true
readiness_scripts_changed: false
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: cumulative documentation compatibility only
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
search_commands_bounded: n/a
```

## Application boundary

This patch is based on the working tree where both
`0287-r7-r15-r2-r2-projects-views-actions-readiness-repair` and
`0287-r7-r15-r2-r2-r1-projects-installation-budget-compatibility-fix` are
already applied but uncommitted because their rule suites stopped the patch
queue. It is intended to be applied with `--allow-dirty` so the queue can rerun
all rules and commit the three coherent units together.
