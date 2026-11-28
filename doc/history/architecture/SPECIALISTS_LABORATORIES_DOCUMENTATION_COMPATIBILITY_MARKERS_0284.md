# 0284-r9-r2 — Documentation compatibility markers

## Purpose

The r9 roadmap refresh removed names consumed by older executable architecture
rules. The initial r1 repair also attempted to modify a historical test whose
local content is not identical to the packaging base.

This replacement avoids that unstable surface. Compatibility is restored in the
documents that the tests inspect:

- `doc/README_CURRENT.md` again exposes the validated 0281 and 0282 markers;
- `templates/github/projects-repository/INSTALLATION.md` keeps `0284-r9` as its
  current version and records the exact `0284-r1-r5` declaration as history.

## Cumulative guide invariant

The first guide declaration remains authoritative:

```text
Version du guide : `0284-r9`.
```

The older sentence appears only after the r9 history table:

```text
Version du guide : `0284-r1-r5`.
```

It is a compatibility marker for the original safe-default rule, not the current
version. Future guide revisions may advance the first declaration while
preserving the historical marker.

## Boundaries

```text
live_path_status: n/a
runtime_modified: false
scheduler_modified: false
sql_modified: false
qdrant_modified: false
openvino_modified: false
github_workflow_modified: false
projects_installation_modified: true
projects_installation_verified: true
external_dependencies_added: false
```
