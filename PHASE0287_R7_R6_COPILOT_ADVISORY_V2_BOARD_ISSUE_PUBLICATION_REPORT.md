# Phase 0287-r7-r6 — Copilot advisory v2 board and Issue publication

## Objective

Close the first user-visible v2 publication boundary while preserving the
existing v1 implementation and every authority gate.

baseline: after 0287-r7-r5
code_rule_review: done
code_rule_update_required: false
live_path_status: controlled-adapter-ready

## Implemented path

```text
request + Copilot v2 + manifest
-> correlated publication preview v2
-> ProjectV2 summary/status/artifact/cycle plan
-> controlled Issue comment plan
-> exact digest confirmation
-> explicit local mutation locks
-> mutation
-> ProjectV2 field readback
-> Issue comment readback
```

The ProjectV2 v2 path reuses the existing `Avis Copilot` generic text field. It
renders all four v2 analytical values into one bounded deterministic summary.
It does not write the historical `Route Copilot` or `Confiance Copilot` fields.

## Authority boundary

- the request remains authoritative;
- the advisory remains untrusted and hint-only;
- an operator `approve` decision is required;
- remote mutation requires explicit environment locks and exact plan digest;
- workflow production never self-authorizes publication;
- Issue replay is a no-op and marker collisions fail closed.

## Deployment review

The Projects bundle gains two v2 scripts and the cumulative installation guide
is updated. No new secret, workflow permission, Scheduler, database or service
is introduced.

## Remaining limitation

Both adapters perform immediate readback. Evidence against the real private
ProjectV2 and the complete GitHub-to-local closed loop remains part of the later
real deployment smoke.
