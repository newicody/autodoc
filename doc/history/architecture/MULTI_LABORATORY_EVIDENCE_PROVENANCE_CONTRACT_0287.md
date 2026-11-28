# Multi-laboratory evidence provenance contract

## Binding

```text
r2 evidence item
+ LaboratoryVisitRequest
+ LaboratoryVisitResult
→ validated laboratory/visit/specialist/source provenance
```

For a cross-laboratory target visit:

```text
SpecialistTransferRequest
+ SpecialistTransferVisitPlan
+ SpecialistTransferResult
+ target LaboratoryVisitRequest/Result
→ transfer-continuous provenance
```

## Aggregate validation

Every r2 item must have exactly one provenance with matching `evidence_ref`,
`specialist_ref` and `source_ref`. The aggregate is multi-laboratory only when
at least two distinct `laboratory_ref` values are present.

R3 validates provenance but does not deduplicate content, interpret claims,
weight evidence, write SQL or authorize Scheduler selection.
