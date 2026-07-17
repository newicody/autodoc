# 0287-r7-r2-r3 — Copilot v2 producer test migration

Corrective sub-revision to apply on the dirty working tree that already contains
`0287-r7-r2-r1` and `0287-r7-r2-r2`.

## Purpose

The full suite still had three executable tests that supplied the historical
Copilot advisory v1 response to the active v2 producer. This patch migrates
those producer fixtures and assertions to `missipy.github.copilot_advisory.v2`.

Historical v1 extraction tests remain unchanged. No v1-to-v2 semantic mapping
is introduced.

## Scope

Modified:

- `tests/tools/test_github_copilot_advisory_optional_0277.py`;
- `tests/tools/test_github_copilot_advisory_response_extraction_0279.py`;
- `tests/tools/test_github_dual_artifact_actions_workflow_0275.py`.

Added:

- phase report;
- changelog;
- architecture Markdown and DOT;
- manifest;
- rule test.

Not modified:

- production runner or manifest builder;
- `templates/github/projects-repository/INSTALLATION.md`;
- Scheduler, laboratories, SQL, Qdrant, OpenVINO or ProjectV2 mutation paths.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-r3-copilot-v2-producer-test-migration \
  --dry-run \
  --allow-dirty
```

Then use `--commit --push --allow-dirty` after a green dry-run.
