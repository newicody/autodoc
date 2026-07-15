# Phase 0286-r4-r1 — ProjectV2 cumulative rule compatibility fix

## Result

Two historical rules were still written as snapshots of earlier bundle states:

- the 0284 rule required the original seven views to be the complete set;
- the 0286-r1 audit rule required the specialist revision fields to remain absent.

The r4 bundle correctly adds one view and nine fields, so both historical rules
now validate preservation plus additive completion instead of forbidding later
phases.

## Boundaries

No runtime, Scheduler, SQL, Qdrant, EventBus, laboratory, workflow, permission,
secret, variable, form, field or view is changed by this corrective patch.
GitHub Projects remains non-authoritative.

## INSTALLATION.md review

The cumulative guide is already updated to `0286-r4`. No update is required for
this rule-only correction because the deployed `newicody/projects` bundle does
not change. The safe Copilot default and the prohibition on `--delete` remain
required.

## Next phase

The next functional patch remains
`0286-r5-specialist-capability-growth-projects-publication-plan`.
