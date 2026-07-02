# Changelog — Phase 7.6 Markdown Doc Layout Tooling

## Added

- `tools/markdown_doc_layout.py`
  - Builds a Markdown layout plan.
  - Keeps root `README.md`.
  - Skips `patch/**/README.md`.
  - Classifies root reports, manifests, changelogs and legacy Markdown files.
  - Can apply moves and rewrite Markdown references.

- `tests/tools/test_markdown_doc_layout.py`
  - Covers classification, planning, patch README skipping, move application and reference rewriting.

- `tests/rules/test_markdown_doc_layout_rule.py`
  - Ensures the tool remains stdlib-only and preserves the root README / patch READMEs.

- `doc/maintenance/MARKDOWN_DOC_LAYOUT.md`
  - Documents the Markdown routing policy.

## Not added

- No network.
- No GitHub API.
- No Scheduler change.
- No automatic deletion of referenced docs.
