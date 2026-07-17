# Phase 0287-r7-r15-r3-r16-r1 — Autodoc workflow boundary lock

## Correction

The first r16 retirement bundle encoded the cleanup as a rename from:

```text
.github/workflows/autodoc-controlled-research.yml
```

The operator worktree already lacked that file, so `git apply --check` correctly
rejected the rename.

This corrective unit does not reference or recreate the missing workflow. It
adds only the repository boundary rule and documentation.

## Commit behavior

When the missing workflow is a tracked local deletion, the existing Patch Queue
commit step discovers it through `git diff --name-only`, stages it together
with the additive r16-r1 files and commits the deletion.

If the deletion is already committed locally, this unit simply adds the
boundary evidence.

## Canonical flow

```text
newicody/projects workflow
→ authoritative_request
→ copilot_advisory
→ dual_artifact_manifest
→ local Autodoc fetch/import
→ durable intake and controlled execution
```

No active repository workflow belongs in `newicody/autodoc`.
