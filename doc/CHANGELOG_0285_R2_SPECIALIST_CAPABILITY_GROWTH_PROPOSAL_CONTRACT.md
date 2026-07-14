# Changelog — 0285-r2 specialist capability growth proposal contract

Patch: `0285-r2-specialist-capability-growth-proposal-contract`

## Added

- `SpecialistCapabilityEvidenceRef`, an immutable digest-bound evidence reference;
- `SpecialistCapabilityGrowthProposal`, an immutable evidence-backed proposal;
- deterministic proposal projection and SHA-256 digest;
- validation of specialist, capability, contract and evidence continuity;
- explicit non-authoritative and non-dispatchable projection flags;
- context and architecture tests;
- architecture document, DOT graph, phase report and manifest.

## Unchanged boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority.
- Qdrant remains projection and recall only.
- EventBus remains observation only.
- no backend, storage adapter, network call or Projects deployment change.

## Next

`0285-r3-portable-specialist-revision-lineage-contract`
