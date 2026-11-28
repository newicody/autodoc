# Changelog — Phase 7.13 Documentation SVG Build Policy

## Added

- `tools/docs_svg_build_policy.py`
  - Scans generated SVG files under `doc/docs/architecture`.
  - Treats `doc/docs/architecture/context/*.svg` as source-only generated files.
  - Supports dry-run, cleanup, check and JSON report output.

- `tests/tools/test_docs_svg_build_policy.py`
  - Covers source-only detection, dry-run, cleanup, assertion failure and rendering.

- `tests/rules/test_docs_svg_build_policy_rule.py`
  - Ensures the policy tool remains local-only and does not modify the makefile.

- `doc/maintenance/DOCS_SVG_BUILD_POLICY.md`
  - Documents the safe `make` then clean/check workflow.

## Not added

- No makefile rewrite.
- No network.
- No Scheduler change.
- No SVG versioning policy change.
