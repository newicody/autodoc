# Phase 0286-r7-r1 — readback artifact-chain correction

Status: corrective patch complete.

The original r7 invocation assumed that two prerequisite files already
existed. The repository had no local fixture builder, and the r6 CLI could not
persist its result. This patch closes that operational gap:

- r6 accepts `--output` and writes the complete JSON report;
- r7 checks every input path before any GitHub query;
- a local-only fixture builder produces the four files needed to test r7;
- fixture evidence can only establish `snapshot_ready`, never deployment
  readiness or a real GitHub publication.

`templates/github/projects-repository/INSTALLATION.md` reviewed.
No update required: no file deployed into `newicody/projects` changes.
