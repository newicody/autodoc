# Phase 0287-r1 — multi-laboratory evidence aggregation reuse audit

Status: reuse audit complete.

Existing contracts already provide laboratory/visit identity, evidence
references, provenance references, specialist conversation continuity,
cross-laboratory transfer continuity, digest-bound evidence claims, explicit
operator decisions, an append-only SQL-authority history pattern and passive
observation patterns.

The missing capability is a canonical immutable multi-laboratory evidence
aggregate. It must preserve per-laboratory provenance, deduplicate by digest,
surface contradictions, accept only operator-authorized weighting and remain
non-authoritative until recorded in SQL and selected by the existing Scheduler.

No new Scheduler, LaboratoryManager, global evidence registry, EventBus,
Qdrant authority or GitHub authority is required.

INSTALLATION.md reviewed.
No update required for 0287-r1: the audit adds no workflow, Issue form,
ProjectV2 field/view, secret, variable or file deployed into
`newicody/projects`.
