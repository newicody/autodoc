# Phase 0286-r1 — specialist capability growth Projects operator workflow reuse audit

## Status

Implemented as a source-only, deterministic audit. The current 0285 generic chain is reused in full. GitHub Projects remains a workflow, review and publication surface; it does not become the authority for specialist revisions.

## Reuse decision

- Reuse the r2 proposal, r3 lineage, r4 operator gate, r5 SQL-authoritative history, r6 Scheduler selection, r7 observation and r8 smoke.
- Reuse `github_controlled_advisory_issue_publication_0281.py` for digest-bound idempotent Issue publication.
- Reuse `apply_github_project_v2_operator_authorized_mutations_0282.py` and its preview/execute/confirmed-digest boundary.
- Reuse the existing query-only ProjectV2 readback and append-only cycle lineage patterns.
- Do not create another Scheduler, global specialist registry, EventBus, HTTP client or `LaboratoryManager`.

## Confirmed gaps

1. No immutable Projects review projection exists for one 0285 proposal/revision/decision/history selection.
2. Generic research/update/theme forms do not express a capability-growth request precisely.
3. `projectv2_views.json` has no specialist revision, capability decision or dedicated review view.
4. No controlled publication plan binds the Issue comment and ProjectV2 field projection to the same digest.
5. No query-only readback proof closes the local-authority/remote-projection loop.

## Safety boundary

The existing controlled workflow has `issues: read` and `actions: read`; it must not be turned into an approval authority. Operator approval remains the local r4 decision. SQL remains durable authority, Scheduler remains the only orchestrator, Qdrant remains projection/recall and Copilot remains advisory.

## newicody/projects installation review

`templates/github/projects-repository/INSTALLATION.md reviewed` at version `0284-r9`. `No update required for 0286-r1`: this audit adds no workflow, form, ProjectV2 field, variable, secret, permission or deployment command. The guide must be updated cumulatively starting with the first bundle-changing patch.

## Next patch

`0286-r2-specialist-capability-growth-projects-review-projection-contract`
