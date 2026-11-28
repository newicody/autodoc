# Changelog — 0162 GitHub external artifact smoke

0162 adds a local-only smoke that corrects the artifact source boundary after
the local patch-ingestion detour.

## Added

- `tools/run_github_external_artifact_smoke.py`
- tool tests for accepting an external GitHub artifact and rejecting the
  Autodoc development repository as idea source
- rule tests
- architecture doc
- code rule
- runtime DOT source
- manifest
- phase test report

## Boundary

No runtime Python under `src/` is modified.

No SQL, Qdrant, GitHub API, external network, Scheduler, LLM or OpenVINO
execution is introduced.
