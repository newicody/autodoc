# Phase 0285-r3 — portable specialist revision lineage contract report

Date: 2026-07-14

## Objective

Define the immutable revision and lineage contracts required after an evidence-backed
capability-growth proposal and before the explicit operator gate.

## Result

The phase adds `PortableSpecialistRevision` and `SpecialistRevisionLineage` while
reusing the existing `PortableSpecialistDescriptor` as the complete descriptor
snapshot. One stable `specialist_ref` is preserved across a deterministic,
append-only, single-parent lineage.

The root revision bootstraps an existing descriptor. Every later revision requires a
typed proposal reference, the deterministic proposal digest and at least one typed
evidence reference. A pure validator correlates the revision with the existing r2
proposal and the parent revision. Approval is not embedded. No Scheduler selection, SQL write,
Qdrant projection, EventBus publication, GitHub mutation, provider binding or runtime
execution occurs.

## Validation

- targeted context and architecture tests: **19 passed**;
- `compileall`: passed;
- `git diff --check`: passed;
- `git apply --check` on an isolated base: passed;
- patch is addition-only.

## Next phase

`0285-r4-specialist-capability-growth-operator-gate`
