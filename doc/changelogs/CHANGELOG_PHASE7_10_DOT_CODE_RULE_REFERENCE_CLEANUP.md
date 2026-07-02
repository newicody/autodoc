# Changelog — Phase 7.10 DOT code_rule Reference Cleanup

## Added

- `tools/dot_remove_code_rule_references.py`
  - Scans DOT architecture files.
  - Removes lines mentioning `code_rule`, `code-rule` or `code rule`.
  - Writes a JSON cleanup report.
  - Provides a `--check` mode.

- `tests/tools/test_dot_remove_code_rule_references.py`
  - Covers line removal, fixture application, assertion failure and assertion pass.

- `tests/rules/test_dot_code_rule_cleanup_rule.py`
  - Ensures the cleanup is local-only and DOT-scoped.

- `doc/maintenance/DOT_CODE_RULE_CLEANUP.md`
  - Documents dry-run, apply and validation commands.

## Not added

- No SVG rewriting.
- No network.
- No GitHub API.
- No Scheduler change.
