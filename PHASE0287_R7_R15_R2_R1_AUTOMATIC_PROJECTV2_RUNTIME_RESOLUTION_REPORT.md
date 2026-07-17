# Phase 0287-r7-r15-r2-r1 — Automatic ProjectV2 and runtime resolution

## Objective

Correct the operator boundary exposed by r15-r2. The preview command must not
require an operator to discover GraphQL node identifiers or repeat stable local
configuration on every run.

The corrected flow is:

```text
RUN_ID + repository + promote/merge decision
→ read existing local ProjectV2 configuration
→ load one configured real-runtime factory reference
→ download and validate the three Actions artifacts
→ derive the source Issue from the authoritative request
→ resolve the exact ProjectV2 and Issue item by read-only GraphQL
→ resolve the configured field by exact name
→ execute r14 on the attested real ports
→ mandatory r15-r1 preview
→ write the correlated JSON and resolved target metadata
```

No Issue comment or ProjectV2 mutation is performed.

## Reuse audit

The patch reuses:

- `.var/config/github_project_v2_query_only.ini` as the ProjectV2 owner, number
  and GitHub token-name authority;
- the authoritative request as the source-Issue authority;
- `GitHubCliFinalDeliverablePublicationAdapter` as the existing GraphQL
  transport boundary;
- the r15-r2 `ImportedActionsRuntimePorts` contract and dynamic factory loader;
- the r14 composition and r15-r1 preview without copying their logic.

The new pure resolver under `src/context` selects one exact project, item and
field from a GraphQL mapping. It does not import subprocess, environment,
configuration, GitHub SDKs or runtime backends.

## Operator boundary

The normal command becomes:

```bash
python tools/run_love_actions_closed_loop_0287.py \
  --run-id "$RUN_ID" \
  --repository newicody/projects \
  --candidate-decision promote \
  --format text
```

The following low-level options are no longer required:

```text
--project-item-id
--project-field-ref
--project-field-name
--project-owner
--project-number
--runtime-factory
```

They remain diagnostic overrides only.

## One-time local configuration

Project owner, number and token environment are read by default from:

```text
.var/config/github_project_v2_query_only.ini
```

The real runtime factory is installation-specific and remains explicit. It is
configured once in:

```text
.var/config/love_actions_closed_loop.ini
```

from `config/love_actions_closed_loop.example.ini`:

```ini
[runtime]
factory = package.module:build_runtime
```

The environment override `AUTODOC_LOVE_RUNTIME_FACTORY=module:function` remains
available. There is no module search, guessed factory or dummy fallback.

## Exact ProjectV2 resolution

After validating the downloaded request, the CLI obtains its `issue_number` and
performs one read-only GraphQL query that returns:

- the Issue's ProjectV2 items;
- the configured user- or organization-owned ProjectV2;
- that project's fields.

The pure resolver requires exactly one configured project, one Issue item in
that project and one field with the configured name. Missing or ambiguous
matches fail before SQL, OpenVINO, Qdrant or the Scheduler are invoked.

The resolved identifiers are stored under `_r15_resolution` in the output JSON
for audit and later replay, but the operator does not need to discover or export
them.

## Failure behavior

All configuration and command construction now occur inside the CLI error
boundary. Missing project configuration, missing runtime factory, malformed
values, absent ProjectV2 membership and ambiguous fields return `error: ...`
with exit status 2 instead of a Python traceback.

If the Issue is absent from the configured project, the error explicitly states
that the source Issue is not present exactly once. The patch does not silently
add the Issue because that would be a remote mutation before preview approval.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing configuration, typed resolver and adapter boundaries are sufficient
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

The patch adds no new transport or network authority. It extends the existing
GitHub CLI GraphQL adapter with a read-only resolver operation.

## Validation

Tests cover exact project/item/field selection, optional low-level CLI
arguments, configuration precedence, reuse of the existing ProjectV2 config,
clear missing-runtime failure, atomic diagnostic overrides and source-only DOT.

## Next phase

`0287-r7-r15-r3` can now focus on the concrete installed runtime factory and the
actual preview/publication/readback evidence instead of manual GraphQL plumbing.
