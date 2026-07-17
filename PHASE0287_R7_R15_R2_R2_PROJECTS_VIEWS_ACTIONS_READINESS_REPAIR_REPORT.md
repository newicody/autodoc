# Phase 0287-r7-r15-r2-r2 — Projects views and Actions readiness repair

## Objective

Repair the installation boundary of the copied `newicody/projects` bundle before
attempting live r15 evidence. A named ProjectV2 view is not considered compliant
merely because its name exists, and an Actions workflow is not considered ready
merely because repository Actions are globally enabled.

The read-only audit now compares the declared bundle with the current remote
state:

```text
projectv2_views.json
+ current ProjectV2 fields, options and views
+ workflow source
+ repository Actions policy
+ selected-actions policy
+ workflow state
+ Copilot advisory variable
→ exact readiness report
```

No field, view, workflow, variable, permission, Issue or ProjectV2 item is
modified by this patch.

## Reuse audit

The patch reuses:

- `projectv2_views.json` as the declarative ProjectV2 target;
- `reconcile_projectv2_configuration.py` for the existing controlled creation
  plan and digest gate;
- the copied `autodoc-controlled-research.yml` as the workflow source authority;
- GitHub CLI as the already selected GitHub transport;
- the repository's selected-Actions configuration and GitHub variable as remote
  readback authorities;
- `templates/github/projects-repository/INSTALLATION.md` as the cumulative
  installation guide.

It adds one pure comparison contract and one thin read-only CLI adapter. It does
not add an alternate reconciler or mutation path.

## Exact ProjectV2 readiness

For each declared field the report verifies:

- one unique field with the expected name;
- exact data type;
- exact single-select options, including missing and unexpected options.

For each declared view the report verifies:

- one unique view with the expected name;
- exact layout;
- exact filter;
- exact visible fields and order;
- exact board column field;
- exact vertical grouping field.

An existing name with a wrong filter, layout or grouping is therefore reported
as drift instead of being classified as installed.

## Actions readiness

The report reads:

- repository Actions enablement and `allowed_actions` mode;
- selected-Actions settings when required;
- SHA pinning policy;
- every `uses:` reference in the copied workflow;
- remote workflow state;
- manual and automatic triggers;
- `AUTODOC_COPILOT_ADVISORY_ENABLED`;
- the declared `copilot-requests: write` permission.

It separates two statuses:

```text
authoritative_ready
  request and authoritative artifact path can run

copilot_ready
  optional Copilot advisory path can run
```

Copilot being explicitly disabled is visible but does not fail the authoritative
path. The CLI exits successfully when the authoritative path is ready, while
`full_ready` remains false until both ProjectV2 and Copilot readiness are true.

## Installation repair

The cumulative guide no longer contains an empty or placeholder digest. It now
records the real sequence:

```text
preview reconciliation
→ extract .plan_digest
→ require a non-empty value
→ execute the unchanged plan with that exact digest
```

It also documents the new exact readback command and the selected-Actions
inspection required when `allowed_actions=selected`.

## Mutation boundary

The new command has no `--execute` option and issues only read operations:

- GraphQL query for ProjectV2 fields and views;
- REST GET for Actions permissions;
- REST GET for selected-Actions settings;
- REST GET for workflow state;
- REST GET for the Copilot variable.

The returned mapping always records:

```text
remote_mutation_allowed: false
mutation_performed: false
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing declarative configuration and GitHub CLI boundaries are sufficient
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: true
github_api_added: true
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```

Network access is query-only GitHub readback. No production execution backend is
introduced, so this patch remains a transition/readiness proof rather than live
closed-loop evidence.

## Validation

Tests cover:

- exact fields, options and views;
- drift hidden behind an existing view name;
- selected-Actions policy;
- GitHub-owned Action allowance;
- SHA pinning failure;
- Copilot-disabled authoritative readiness;
- read-only end-to-end report construction;
- absence of mutation surfaces;
- cumulative installation guide requirements;
- source-only DOT and mandatory code-rule metadata.

## Remaining manual boundary

The existing reconciler still creates only missing supported resources. When
GitHub exposes a current view as drifted but does not provide a supported update
mutation for that property, the readiness report identifies the exact mismatch
for correction in the GitHub interface. It never silently declares the view
compliant.

## Next phase

`0287-r7-r15-r3-r1` must compose the canonical installed runtime factory for the
existing Scheduler, SQL authority, OpenVINO/E5-384 and Qdrant ports. Once the
bundle readback is authoritative-ready, r15 can proceed to mandatory live
preview evidence.
