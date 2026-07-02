# Phase 7.6 — Markdown Doc Layout Tooling

Phase 7.6 adds tooling to inventory and reorganize Markdown documentation.

The tool keeps the root `README.md` in place, skips patch bundle READMEs, moves
root reports/manifests/changelogs into `doc/` subdirectories, and rewrites
Markdown references after moving files.

This phase adds the controlled tool first. The actual repository-wide migration
can then be run locally and reviewed as a separate commit if the plan is correct.
