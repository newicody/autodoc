# Changelog — 0164 GitHub read-only artifact fetch smoke

0164 adds a local-only smoke for the GitHub read-only artifact fetch/import
boundary.

## Added

- `tools/run_github_read_only_artifact_fetch_smoke.py`
- tool tests
- rule tests
- architecture doc
- code rule
- runtime DOT source
- manifest
- phase test report

## Boundary

0164 uses existing read-only/projection builders and does not create a new
GitHub adapter. It does not call GitHub, does not use external network, does
not write SQL/Qdrant, and keeps the remote mutation gate closed.
