# Phase 0287-r3 — multi-laboratory evidence provenance contract

Status: immutable provenance contract complete.

Each r2 evidence item can now be bound to an existing laboratory visit. The
factory reuses `validate_laboratory_visit_result`, requires a completed visit,
checks the specialist identity and requires the evidence reference to be
present in the visit result.

For cross-laboratory visits, the complete existing specialist transfer request,
visit plan and result are mandatory and are checked with
`validate_specialist_transfer_chain`. Aggregate validation now proves at least
two distinct `laboratory_ref` values rather than merely two opaque provenance
references.

Deduplication, contradictions, weighting, SQL history, Scheduler selection and
observation remain outside r3.

INSTALLATION.md reviewed.
No update required for 0287-r3: no workflow, Issue form, ProjectV2 field/view,
secret, variable or file deployed into `newicody/projects` changes.
