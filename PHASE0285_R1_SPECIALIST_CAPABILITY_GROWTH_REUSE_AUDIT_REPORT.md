# Phase 0285-r1 — specialist capability growth reuse audit report

Status: ready for application after `0284-r9-r2-specialists-laboratories-documentation-compatibility-markers`.

## Purpose

Audit the existing portable-specialist, laboratory, Scheduler, memory, observation,
and GitHub surfaces before adding any capability-growth contract.

The result is deliberately source-only. It does not import the audited modules,
construct a runtime, contact a backend, mutate SQL/Qdrant, publish an EventBus
message, or call GitHub.

## Reuse findings

1. `PortableSpecialistDescriptor` already owns stable `specialist_ref`,
   `specialist_version`, capability contracts, input/output contracts, execution
   profiles, and allowed laboratory bindings.
2. `ContextTrajectoryStep.capability_hint` and the exploration budget already
   express capability demand without adding a specialist registry.
3. Existing Scheduler deliberation and specialist-dispatch contracts are the only
   orchestration boundary.
4. Laboratory descriptors already advertise capabilities; a laboratory must not
   approve a specialist revision.
5. Specialist/laboratory messages and transfer contracts already preserve
   evidence, conversation, context, visit, origin, target, and return-route refs.
6. Phase 0284 already provides the real SQL/OpenVINO/Qdrant evidence boundary:
   SQL remains authoritative and Qdrant returns references only.
7. EventBus, PassiveSupervisor, and Cell Lens already provide passive observation.
8. GitHub Projects and Copilot are review/workflow/advisory surfaces, not the
   durable authority and not an approval authority.

## Missing chain

The missing architecture is:

`proposal → evidence → operator decision → immutable revision → durable history → approved Scheduler selection → passive observation → closed-loop smoke`

This chain must extend the existing portable descriptor. It must add no global
specialist registry, no learning daemon, no `LaboratoryManager`, and no parallel
Scheduler.

## Locked boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable authority.
- Qdrant remains projection and recall only.
- EventBus remains observation only.
- `/dev/shm` remains the fast local data plane, never the durable capability authority.
- A specialist cannot authorize its own capability growth.
- A laboratory cannot authorize specialist capability growth.
- Copilot cannot authorize specialist capability growth.
- GitHub remains a controlled review and workflow surface.
- Capability evidence may propose a revision but cannot mutate the active descriptor.

## Roadmap decision

The first missing unit is:

`0285-r2-specialist-capability-growth-proposal-contract`

The complete controlled sequence is documented in
`doc/architecture/SPECIALIST_CAPABILITY_GROWTH_DEVELOPMENT_PLAN_0285.md`.

## `newicody/projects` installation verification

- INSTALLATION reviewed: yes
- INSTALLATION modified: no
- Reason: no Projects deployment surface changes in 0285-r1.
- Expected current guide: `0284-r9`.
- Safe default remains `AUTODOC_COPILOT_ADVISORY_ENABLED=false`.
- The cumulative no-`--delete` deployment rule remains mandatory.

## Deliverable validation target

- source compilation;
- context tests for deterministic source-only auditing;
- architecture rules for no parallel runtime and no execution switch;
- cumulative installation-guide verification;
- `git diff --check`;
- `git apply --check` against the expected post-0284-r9-r2 base.
