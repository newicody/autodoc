# Phase 0286-r2 — Specialist capability-growth Projects review projection

## Result

Status: **green**.

The phase adds one immutable review projection derived from the already-closed
0285 capability-growth evidence.  It preserves proposal, revision, operator
decision, SQL history, Scheduler selection, laboratory route and passive
observation correlations without publishing or mutating GitHub.

## Reused surfaces

- 0285 closed-loop smoke mapping and digest;
- operator-approved decision and revision lineage;
- SQL-authoritative history references;
- existing Scheduler selection;
- EventBus and PassiveSupervisor observation evidence;
- the established controlled GitHub publication boundaries reserved for later
  0286 phases.

## Boundaries

- GitHub Projects is a review surface, never durable authority;
- no Issue comment or ProjectV2 mutation is performed;
- SQL remains durable authority;
- Scheduler remains the only orchestrator;
- Qdrant remains projection/recall only;
- Copilot remains advisory;
- no Scheduler, registry, HTTP client or LaboratoryManager is added.

## Validation

- contract tests: 11 passed;
- architecture-rule tests: 6 passed;
- compileall: passed;
- deterministic digest: passed;
- addition-only patch application: passed.

## Installation review

`templates/github/projects-repository/INSTALLATION.md` was reviewed.  No update
is required in 0286-r2 because the Projects bundle, workflows, forms, fields,
views, variables, secrets and permissions are unchanged.  The cumulative guide
will be updated in 0286-r3 when the dedicated Issue form is added.
