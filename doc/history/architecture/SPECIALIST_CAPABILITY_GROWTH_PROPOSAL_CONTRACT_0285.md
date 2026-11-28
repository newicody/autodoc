# 0285-r2 — Specialist capability growth proposal contract

Patch: `0285-r2-specialist-capability-growth-proposal-contract`

## Purpose

Phase 0285-r2 introduces the first missing contract from the 0285-r1 reuse
audit: an immutable, evidence-backed proposal that cannot authorize itself.

```text
existing execution / observation / report artifacts
              │
              ▼
SpecialistCapabilityEvidenceRef
              │ one specialist_ref + one capability + SHA-256
              ▼
SpecialistCapabilityGrowthProposal
              │ non-authoritative
              ▼
future operator decision (0285-r4)
```

## Invariants

1. `specialist_ref` remains the stable identity used by the existing portable
   specialist descriptor.
2. Every proposal targets exactly one capability and one base specialist
   version.
3. Every proposal carries at least one digest-bound evidence reference.
4. Evidence specialist and capability identities must match the proposal.
5. A proposal contains no approval state and cannot enable Scheduler dispatch.
6. The contract performs no SQL write and no Qdrant projection.
7. The contract does not load OpenVINO, an LLM, GitHub or any runtime backend.
8. Scheduler remains the only orchestration authority.
9. SQL remains the durable authority.
10. Qdrant remains projection and recall only.

## Why references, not payloads

The contract transports typed references and digests rather than execution
payloads. Durable evidence can later be resolved through the existing authority
boundaries. This keeps the proposal deterministic, replayable and independent
from a particular laboratory implementation.

## Authority model

A specialist, laboratory, operator-facing system or Copilot may formulate a
proposal. Formulation is not authorization. The proposal projection therefore
states explicitly:

```text
authoritative = false
approved = false
scheduler_dispatch_allowed = false
descriptor_mutated = false
durable_state_written = false
```

The explicit operator decision boundary is scheduled for 0285-r4, after the
revision-lineage contract in
`0285-r3-portable-specialist-revision-lineage-contract`.

## Projects installation review

`templates/github/projects-repository/INSTALLATION.md` was reviewed. This phase
adds no workflow, Issue form, variable, secret, ProjectV2 field or publication
surface, so the cumulative guide is not modified.
