# Specialist capability growth development plan — 0285

## Goal

Allow portable specialists to evolve through explicit, auditable revisions while
preserving current orchestration and storage boundaries.

## Sequence

### 0285-r1 — reuse audit

`0285-r1-specialist-capability-growth-reuse-audit`

Prove which current contracts are reused and lock the no-duplicate boundary.

### 0285-r2 — proposal contract

`0285-r2-specialist-capability-growth-proposal-contract`

Add immutable proposal and evidence-reference contracts. A proposal describes a
requested capability delta and its evidence; it cannot activate anything.

### 0285-r3 — revision lineage

`0285-r3-portable-specialist-revision-lineage-contract`

Add immutable revision identity and parent lineage while preserving stable
`specialist_ref`, declared contracts, laboratory bindings, and deterministic
serialization.

### 0285-r4 — operator gate

`0285-r4-specialist-capability-growth-operator-gate`

Add approve/reject/defer decisions and policy validation. Only an explicit
operator decision can authorize a revision.

### 0285-r5 — durable history

`0285-r5-specialist-capability-growth-durable-history`

Add an append-only SQL-authoritative history port and a deterministic fake adapter
for tests. Qdrant may project references only.

### 0285-r6 — approved Scheduler selection

`0285-r6-scheduler-approved-specialist-revision-selection`

Extend the existing Scheduler path so it selects only an approved revision
compatible with the target laboratory. Do not add a new Scheduler.

### 0285-r7 — passive observation projection

`0285-r7-specialist-capability-growth-observation-projection`

Project proposal, decision, revision, and selection transitions through the
existing EventBus/PassiveSupervisor/Cell Lens observation chain. EventBus remains
observation only.

### 0285-r8 — closed-loop smoke

`0285-r8-specialist-capability-growth-closed-loop-smoke`

Prove:

`evidence → proposal → operator approval → immutable revision → SQL history → Scheduler-approved selection → laboratory execution → passive observation`

The smoke must also prove that rejected/deferred revisions cannot be selected.

## Deferred after the smoke

- real operator UI integration in GitHub Projects;
- controlled publication of revision status;
- multi-laboratory evidence aggregation;
- long-term specialist performance evaluation;
- Chalouf as final integrator scenario.

None of these deferred items may bypass the operator gate or turn GitHub, Qdrant,
EventBus, a laboratory, or Copilot into an authority.
