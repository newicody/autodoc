# Phase 0287-r5 — multi-laboratory evidence contradiction detection

Status: immutable contradiction detection complete.

R5 consumes a valid r4 deduplication proof and detects only explicit,
explainable incompatibilities:

- support versus opposition for the same claim value;
- different positive values for a policy-declared single-valued claim;
- policy-declared mutually exclusive value pairs;
- incompatible interpretations attached to the same content digest.

Every contradiction remains unresolved and carries stable evidence, canonical,
source, laboratory and specialist references. R5 does not choose a winner,
apply weights, write SQL, select through Scheduler or publish observations.

The cumulative `newicody/projects` installation guide was reduced from a long
phase-by-phase log to one operational procedure. It now explains that Actions
creates `GITHUB_TOKEN` automatically, that local tools can reuse the active
`gh` credential, that `AUTODOC_PROJECT_TOKEN` is a local alias, and that the
current workflow does not require `AUTODOC_COPILOT_TOKEN`.
