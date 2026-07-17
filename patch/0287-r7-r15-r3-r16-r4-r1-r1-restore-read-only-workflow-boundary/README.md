# 0287-r7-r15-r3-r16-r4-r1-r1-restore-read-only-workflow-boundary

## Cause

The preceding r16-r4-r1 patch moved GitHub Issue publication into the
`newicody/projects` workflow and changed `issues: read` to `issues: write`.

That contradicts four established repository rules:

- the workflow is an artifact producer only;
- it cannot self-authorize remote publication;
- Issue publication remains behind the existing local controlled adapter;
- ProjectV2 qualification and GitHub mutation remain separate boundaries.

## Correction

This patch is the exact functional rollback of
`0287-r7-r15-r3-r16-r4-r1-automatic-inference-copilot-issue-comment`.

It:

- restores `issues: read`;
- removes automatic comment planning/execution from the workflow;
- restores the original three artifact upload steps;
- removes the incorrect documentation and rule added by r16-r4-r1.

It does not remove the existing local v2 Issue comment planner or adapter.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-r1-r1-restore-read-only-workflow-boundary \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r16-r4-r1-r1-restore-read-only-workflow-boundary \
  --commit \
  --push \
  --allow-dirty
```

This patch is intentionally designed to apply on top of the dirty working tree
left by the failed r16-r4-r1 apply attempt.

## Next unit

The following unit will compose the already fetched local `ready_runs` with the
existing idempotent Issue-comment adapter. Remote mutation will occur only from
the local connector with explicit gates, never from the GitHub workflow.
