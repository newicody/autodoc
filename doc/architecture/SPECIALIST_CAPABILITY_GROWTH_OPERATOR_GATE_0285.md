# Specialist capability growth operator gate — 0285-r4

## Decision

Phase 0285-r4 adds the explicit human authority boundary between an immutable
capability-growth candidate and the future durable history.

```text
r2 evidence-backed proposal
          +
r3 candidate revision + current lineage head
          │
          ▼
SpecialistCapabilityGrowthOperatorGate
          │ explicit operator: reference
          ├── approve → revision authorization only
          ├── reject  → terminal refusal
          └── defer   → non-terminal review state
          │
          ▼
0285-r5 SQL-authoritative append-only history
```

The gate reuses `SpecialistCapabilityGrowthProposal`,
`PortableSpecialistRevision`, `SpecialistRevisionLineage`, and
`validate_revision_against_growth_proposal`. It does not create a parallel
specialist descriptor, registry, manager or orchestration loop.

## Policy validation

Before approval, the gate verifies:

1. proposal, parent lineage and candidate preserve the same `specialist_ref`;
2. the candidate extends the current lineage head with the next revision number;
3. the proposal digest and evidence references match the candidate revision;
4. requested contracts and laboratory capabilities are represented by the descriptor;
5. the configured minimum evidence count and evidence kinds are satisfied;
6. optional distinct-source, operator allow-list and separation-of-duty policies;
7. optional deprecation and restoration policy switches.

A candidate with policy issues cannot receive `approve`. It may still receive an
explicit `reject` or `defer` decision carrying the issues for future durable history.

## Authority split

- **Scheduler remains the only orchestration authority.** An approved decision is not
  a Scheduler selection and performs no dispatch.
- **SQL remains the durable authority.** This phase writes no history; r5 will add the
  append-only history port.
- **Qdrant remains projection and recall only.** No vector or revision authority is
  introduced here.
- **EventBus remains observation only.** No event is published by the contract.
- Laboratories, specialists and Copilot cannot approve; `operator_ref` must use the
  explicit `operator:` reference family.
- GitHub Projects remains a future review surface and receives no mutation in r4.

## Determinism and immutability

Both the gate policy and the decision are frozen, slots-based dataclasses. Canonical
JSON projections produce deterministic SHA-256 policy and decision digests. A decision
binds the proposal digest, candidate revision digest, base lineage digest and policy
digest so r5 can retain a verifiable append-only record.

## Projects installation review

`templates/github/projects-repository/INSTALLATION.md` was reviewed. No update is
required because r4 adds no workflow, Issue form, variable, secret, ProjectV2 field or
publication surface. Copilot remains disabled by default and repository synchronization
must still avoid `--delete`.

## Next phase

`0285-r5-specialist-capability-growth-durable-history` will add the SQL-authoritative,
append-only history port and a deterministic in-memory adapter for tests. It must record
proposal, decision and revision references without turning Qdrant into authority.
