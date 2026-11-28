# Multi-laboratory evidence aggregation — reuse audit

## Reusable surfaces

- `LaboratoryVisitResult` already carries `evidence_refs`,
  `provenance_refs`, `visit_ref` and `laboratory_ref`.
- specialist/laboratory messages preserve conversation and context continuity.
- transfer contracts preserve origin, target, source visit and target visit.
- capability-growth evidence references are digest-bound and typed.
- the operator gate supplies explicit approve/reject/defer authority.
- 0285 provides SQL-history and passive-observation patterns.
- 0286 proves that GitHub Projects remains a non-authoritative workflow layer.

## Missing surface

The repository does not yet have one canonical aggregate that can answer:

- which laboratory and visit produced each claim;
- whether two references point to the same content;
- whether claims contradict one another;
- which weighting decision was explicitly approved;
- which aggregate revision is durable and Scheduler-selectable.

The next patch is
`0287-r2-multi-laboratory-evidence-aggregation-contract`.

## Non-goals

No new runtime provider, transport, Scheduler, `LaboratoryManager`, global
evidence registry, SQL backend, Qdrant collection or GitHub mutation is added
by the audit.
