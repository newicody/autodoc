# Portable specialist revision lineage contract — 0285-r3

## Decision

The existing `PortableSpecialistDescriptor` remains the complete portable specialist
snapshot. Phase 0285-r3 wraps that descriptor in immutable revisions instead of
creating a second specialist definition or a global specialist registry.

Each lineage preserves one **stable specialist_ref**. Revisions are **append-only**,
numbered from 1, and form a deterministic single-parent chain. The root revision
bootstraps an already known descriptor. A later revision must bind the proposal
reference, proposal SHA-256 digest and evidence references that justify the changed
descriptor snapshot. The pure `validate_revision_against_growth_proposal` function
correlates the revision with the existing r2 proposal and its parent without approving
or persisting anything.

## Authority boundary

The revision contract records structure and provenance only. The operator decision remains external. A revision cannot approve itself, cannot dispatch work and cannot
be selected by the Scheduler merely because it exists.

The following boundaries remain unchanged:

- Scheduler is the only orchestration authority;
- SQL becomes the durable append-only history only in r5;
- Qdrant remains projection and recall by references;
- EventBus, PassiveSupervisor and Cell Lens remain observation-only;
- laboratories, specialists and Copilot cannot authorize capability growth;
- no provider, backend or runtime is attached by this phase.

## Invariants

1. Every revision contains an existing `PortableSpecialistDescriptor`.
2. `specialist_ref` is identical in all revisions.
3. Revision numbers are contiguous and start at 1.
4. Each non-root revision points to the immediately preceding revision.
5. Descriptor versions, descriptor digests, revision references and proposal
   references are unique within a lineage.
6. `head_revision_ref` identifies the final revision.
7. Canonical JSON projections produce deterministic SHA-256 revision and lineage
   digests.
8. Appending returns a new frozen lineage and never mutates the previous value.

## Installation review

`templates/github/projects-repository/INSTALLATION.md` was reviewed. No change is
needed because r3 adds no workflow, Issue form, ProjectV2 field, variable, secret or
remote mutation surface.

## Next phase

`0285-r4-specialist-capability-growth-operator-gate` will introduce the explicit
operator decision boundary. It must consume proposals and revision candidates without
moving approval authority into the specialist, laboratory, Copilot or Scheduler.
