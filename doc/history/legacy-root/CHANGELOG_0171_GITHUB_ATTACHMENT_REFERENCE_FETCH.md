# Changelog — 0171 GitHub attachment reference fetch

- Added network-free context contract for GitHub issue attachment reference fetch records.
- Added `tools/run_github_attachment_reference_fetch_once.py`.
- Added fixture-based tests for resolving referenced attachments into a server dataset.
- Locked the boundary: configured server dataset, no repository user artifacts, no remote mutation, no conversion direct execution.
