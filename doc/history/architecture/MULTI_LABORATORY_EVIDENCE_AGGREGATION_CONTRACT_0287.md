# Multi-laboratory evidence aggregation contract

## Composition

```text
SpecialistCapabilityEvidenceRef (0285)
+ subject_ref
+ opaque provenance_ref
+ structured claim key/value/relation
→ MultiLaboratoryEvidenceItem

at least two distinct provenance refs
→ canonical sorted evidence items
→ MultiLaboratoryEvidenceAggregate
→ deterministic aggregation_digest
```

## Deliberate phase boundaries

R2 does not prove that two provenance references represent two different
laboratories. R3 will validate laboratory, visit, specialist, source and
transfer continuity. R4 will deduplicate repeated content digests. R5 will
detect incompatible claims. R6 will apply operator-authorized weighting.

The aggregate is non-authoritative. It cannot write SQL, select through the
Scheduler, publish EventBus observations or mutate GitHub Projects.
