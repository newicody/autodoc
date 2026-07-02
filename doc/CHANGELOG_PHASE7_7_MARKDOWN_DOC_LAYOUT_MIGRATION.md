# Changelog — Phase 7.7 Markdown Doc Layout Migration

## Added

- `tools/markdown_doc_migrate_repo.py`
  - Applies the Markdown layout plan.
  - Rewrites Python test references to moved Markdown files.
  - Writes a JSON migration report.

- `tests/tools/test_markdown_doc_migrate_repo.py`
  - Covers Python reference rewriting and an end-to-end local migration fixture.

- `tests/rules/test_markdown_doc_migration_rule.py`
  - Ensures the migration remains local-only and imports are stable.

- `doc/maintenance/MARKDOWN_DOC_MIGRATION.md`
  - Documents dry-run, apply and validation commands.

## Not added

- No network.
- No GitHub API.
- No deletion of referenced documentation.
- No Scheduler change.
