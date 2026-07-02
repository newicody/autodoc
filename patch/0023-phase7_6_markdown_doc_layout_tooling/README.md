# 0023 — Phase 7.6 Markdown Doc Layout Tooling

This patch adds local tooling to inventory and reorganize Markdown documentation.

It keeps the root README in place, skips patch bundle READMEs, routes reports /
manifests / changelogs into doc subdirectories, and rewrites Markdown references
when applied.

## Apply patch

```bash
python apply_patch_queue.py --patch 0023-phase7_6_markdown_doc_layout_tooling --dry-run
python apply_patch_queue.py --patch 0023-phase7_6_markdown_doc_layout_tooling --commit --push
```

## After the patch: dry-run the repository layout

```bash
python tools/markdown_doc_layout.py --root . --report-file doc/maintenance/markdown_layout_plan.json
```

## Apply the layout once the plan is reviewed

```bash
python tools/markdown_doc_layout.py --root . --apply --report-file doc/maintenance/markdown_layout_plan.json
```

## Scope

- Add Markdown layout planner/applicator.
- Preserve root README.
- Preserve patch bundle README files.
- Move reports/manifests/changelogs under doc.
- Rewrite Markdown references after moves.
- Add tests and docs.

## Out of scope

- No deletion of referenced docs.
- No network.
- No GitHub API.
- No Scheduler change.
