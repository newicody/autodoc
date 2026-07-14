# Phase 0286-r3-r1 — Request-form audit progression rule fix

## Cause

The 0286-r2 historical rule asserted that the audit must always recommend
`0286-r3-specialist-capability-growth-projects-request-form-contract`.
Once r3 is present, the source-only audit correctly marks r3 completed and
recommends r4, so the historical assertion becomes stale.

## Correction

The r2 rule now accepts both legitimate states:

- before r3: r3 is the next recommended patch;
- from r3 onward: r3 belongs to `completed_phases`.

This is a test-compatibility correction only. It does not modify the 0286 audit,
the request form, the Scheduler, SQL, Qdrant, EventBus, laboratory execution, or
GitHub mutation boundaries.

## Installation review

`templates/github/projects-repository/INSTALLATION.md` remains at `0286-r3`.
No update is required because the deployed Projects bundle is unchanged.
