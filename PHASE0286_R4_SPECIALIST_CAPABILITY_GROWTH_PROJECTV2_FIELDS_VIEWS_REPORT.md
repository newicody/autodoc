# Phase 0286-r4 — Specialist capability-growth ProjectV2 fields and views

## Result

The versioned `newicody/projects` bundle now declares the nine review fields
prepared by the immutable r2 projection and one table view named
`Révisions spécialistes`.

The configuration remains declarative. GitHub Projects is a review and
workflow surface, SQL remains the durable authority, and the existing
Scheduler remains the only orchestration authority. Qdrant remains limited to
projection and recall.

## Scope

- extend `projectv2_views.json` without deleting existing fields or views;
- preserve machine values used by the local r2 review projection;
- reuse the existing preview-first ProjectV2 reconciler;
- update the cumulative `INSTALLATION.md` to `0286-r4`;
- leave workflows, permissions, variables and secrets unchanged.

## Verification

The phase checks JSON validity, field uniqueness, exact option values, the
specialist review view, cumulative installation markers and audit progression
to `0286-r5-specialist-capability-growth-projects-publication-plan`.
