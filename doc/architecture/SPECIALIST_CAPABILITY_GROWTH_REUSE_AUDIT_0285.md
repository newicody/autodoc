# Specialist capability growth reuse audit — 0285-r1

## Decision

Specialist capability growth is not a new subsystem. It is a controlled,
append-only evolution of the existing portable specialist descriptor.

The canonical chain is:

`proposal → evidence → operator decision → immutable revision → durable history → approved Scheduler selection → passive observation`

## Existing surfaces to extend

| Concern | Existing authority/surface | 0285 use |
|---|---|---|
| Portable identity and capabilities | `PortableSpecialistDescriptor` | Preserve `specialist_ref`; advance an immutable version only after approval. |
| Capability demand | `ContextTrajectoryStep.capability_hint` | Explain why a missing/new capability is requested. |
| Orchestration | existing Scheduler deliberation/dispatch | Select approved revisions only. |
| Laboratory compatibility | `LaboratoryDescriptor.capabilities` and bindings | Validate placement; never approve growth. |
| Correlation | specialist/laboratory messages and transfers | Carry proposal, evidence, revision, and decision refs. |
| Durable authority | SQL-backed context/history ports | Store append-only proposal/decision/revision lineage. |
| Vector recall | Qdrant via SQL references | Recall candidate evidence; never become authority. |
| Fast data plane | `/dev/shm` | Carry transient frames; never own revision state. |
| Observation | EventBus, PassiveSupervisor, Cell Lens | Display transitions without commanding them. |
| Human workflow | GitHub Projects | Review/status surface; remote mutation remains controlled. |
| Advisory | Copilot artifact | Evidence/advice only; never approval. |

## Explicit non-goals

- no global specialist registry;
- no self-modifying specialist descriptor;
- no automatic capability learning enabled by evidence alone;
- no new Scheduler or orchestration loop;
- no `LaboratoryManager`;
- no EventBus command channel;
- no Qdrant-authoritative capability state;
- no GitHub-authoritative runtime state;
- no provider/backend implementation in the audit phase.

## Identity and revision invariant

A capability change preserves the stable `specialist_ref`. It creates a new,
immutable specialist revision linked to its parent revision and to the evidence
and operator decision that justified it. A revision is selectable only after an
explicit approved decision.

A rejected or deferred proposal remains in durable history but cannot alter the
active revision.

## Authority split

Scheduler remains the only orchestration authority.

SQL remains the durable authority.

Qdrant remains projection and recall only.

EventBus remains observation only.

The operator gate is the only authority allowed to approve or reject a proposed
capability revision. Policy code may validate a proposal, but it cannot silently
turn evidence into an active specialist capability.

## First implementation unit

`0285-r2-specialist-capability-growth-proposal-contract`

It must be stdlib-only and immutable, and introduce evidence-backed proposal
contracts without a store, runtime adapter, scheduler change, or provider call.
