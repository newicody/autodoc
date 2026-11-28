# Changelog — Phase 7.5 GitHub Export Bundle

## Added

- `src/context/source_candidate_github_export_bundle.py`
  - Builds a local inspection bundle from an external projection contract and GitHub projection payload.
  - Writes a remote mutation gate result.
  - Writes a fake adapter dry-run report.
  - Writes a bundle manifest.

- `tests/context/test_source_candidate_github_export_bundle.py`
  - Covers local bundle writing, open gate recording, manifest reading and invalid policy.

- `tests/rules/test_source_candidate_github_export_bundle_rule.py`
  - Ensures the bundle remains local-only and uses the fake adapter plus gate.

- `doc/docs/architecture/context/63_source_candidate_github_export_bundle.dot`
  - Documents the local GitHub export bundle boundary.

## Not added

- No real GitHub adapter.
- No GitHub API calls.
- No network.
- No token handling.
- No remote mutation.
- No Scheduler change.
