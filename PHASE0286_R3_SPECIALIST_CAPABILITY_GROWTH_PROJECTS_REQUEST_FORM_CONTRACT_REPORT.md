# Phase 0286-r3 — specialist capability-growth Projects request form contract

## Status

Implemented. The deployable `newicody/projects` bundle now contains a dedicated
Issue form for specialist capability-growth requests, and Autodoc contains a
stdlib-only immutable local intake contract.

## Result

- the form captures `specialist_ref`, base version, action, capability, expected
  behavior, preliminary evidence, validation criteria and requested contracts;
- missing evidence or contract references keep the request valid as intake but
  explicitly mark it as not ready for the formal 0285-r2 proposal;
- the form cannot approve a revision or authorize Scheduler/laboratory execution;
- the normalized request accepts the existing authoritative-request artifact,
  a GitHub event or a raw Issue mapping;
- request references and digests are deterministic;
- operator decision remains local.

## Boundaries

```text
projects_bundle_modified: true
projects_installation_modified: true
workflow_modified: false
scheduler_modified: false
sql_modified: false
qdrant_modified: false
openvino_modified: false
eventbus_modified: false
external_dependencies_added: false
```

## Installation

`templates/github/projects-repository/INSTALLATION.md` is updated cumulatively to
`0286-r3`, preserves the historical compatibility markers and documents the
copy, visibility and authority checks for the new form.

## Validation

- focused context and architecture rules;
- stdlib compilation;
- form YAML parsed during package validation;
- `git diff --check` and isolated `git apply --check`.

## Next patch

`0286-r4-specialist-capability-growth-projectv2-fields-views`
