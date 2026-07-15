# Phase 0287-r6 — multi-laboratory evidence operator weighting policy

Status: immutable explicit operator weighting gate complete.

R6 consumes a valid r5 contradiction-detection proof and produces one
digest-bound `approve`, `reject` or `defer` decision.

Approval requires:

- one integer basis-point weight for every canonical evidence reference;
- a policy-defined total, 10,000 basis points by default;
- one explicit disposition for every contradiction;
- weight/disposition coherence for prefer-left, prefer-right, retain-both and
  exclude-both actions.

Every contradiction remains listed as unresolved because r6 performs no
durable resolution. Approval only authorizes the future r7 SQL-history append.

INSTALLATION.md reviewed.
No update required for 0287-r6: no workflow, Issue form, ProjectV2 field/view,
secret, variable or file deployed into `newicody/projects` changes.
