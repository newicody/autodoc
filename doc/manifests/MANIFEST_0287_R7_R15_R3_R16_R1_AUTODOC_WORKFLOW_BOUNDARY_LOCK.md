# Manifest 0287-r7-r15-r3-r16-r1

## Added

- `.github/workflows/README.md`;
- repository workflow boundary rule;
- correction report;
- changelog;
- architecture note and graph;
- manifest.

## Intentionally not included

- no deletion or rename hunk for the already-missing root workflow;
- no disabled archive copy;
- no modification of the canonical Projects template;
- no GitHub remote mutation;
- no Scheduler, laboratory, SQL, OpenVINO or Qdrant modification.

## Expected operator state

Before commit, either:

```text
 D .github/workflows/autodoc-controlled-research.yml
```

or the deletion is already present in local commit history.

The Patch Queue commit includes all non-patch worktree changes, so a tracked
local deletion is committed with this unit.
