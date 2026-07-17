# 0287-r7-r6 — Copilot advisory v2 board and Issue publication

Prerequisite: `0287-r7-r5-product-final-specialist-exchange-synthesis-reuse-audit`
must already be applied.

This patch adds a versioned Copilot v2 publication preview, controlled
ProjectV2 projection with exact field readback, and controlled source-Issue
comment publication with marker collision guard and idempotent replay.

Apply from the `newicody/autodoc` repository root:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r6-copilot-advisory-v2-board-issue-publication \
  --dry-run \
  --allow-dirty
```

After a green dry-run:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r6-copilot-advisory-v2-board-issue-publication \
  --commit \
  --push \
  --allow-dirty
```

Targeted tests:

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_copilot_advisory_v2_issue_publication_0287_r7_r6.py \
  tests/tools/test_copilot_advisory_v2_publication_preview_0287_r7_r6.py \
  tests/tools/test_copilot_advisory_v2_project_fields_0287_r7_r6.py \
  tests/tools/test_publish_github_copilot_advisory_v2_issue_comment_0287_r7_r6.py \
  tests/rules/test_copilot_advisory_v2_board_issue_publication_0287_r7_r6_rule.py
```
