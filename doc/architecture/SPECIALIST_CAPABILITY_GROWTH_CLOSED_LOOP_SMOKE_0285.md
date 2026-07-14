# Specialist capability growth closed-loop smoke — 0285-r8

## Purpose

Close the generic capability-growth chain without introducing another runtime or
orchestrator. The smoke composes already-approved contracts and requires injected
implementations of the existing SQL history port, portable laboratory smoke and
EventBus publication boundary.

## Closed path

1. Validate one evidence-backed r2 proposal and r3 candidate revision.
2. Prove `reject` and `defer` cannot construct an approved r5 history append.
3. Obtain explicit r4 operator approval.
4. Append the approved revision through a durable SQL-authoritative r5 port.
5. Send the r6 selection command through its existing Event/handler contract.
6. Execute the selected descriptor through the 0284-r5 existing Scheduler/laboratory smoke.
7. Publish the r7 passive observation event.
8. Rebuild the r7 PassiveSupervisor read model.
9. Emit one digest-bound r8 result only when every correlation and authority boundary holds.

## Existing laboratory path

`bind_existing_portable_specialist_laboratory_executor()` lazily imports and invokes
`run_portable_specialist_existing_chain_smoke`. It builds the existing
`PortableSpecialistExistingChainSmokeCommand` from the descriptor selected by r6.
The binder does not create a Scheduler or provider; callers inject the already
composed Scheduler, store, embedding/projection/recall dependencies and EventBus.

## Authority matrix

| Surface | r8 role | Authority |
|---|---|---|
| Operator gate | authorize one revision | explicit human policy authority |
| SQL history port | append approved revision | durable authority |
| Scheduler r6 handler | select compatible approved revision | orchestration authority |
| 0284 laboratory smoke | execute selected fake specialist | bounded execution only |
| EventBus / PassiveSupervisor | publish and reconstruct facts | observation only |
| Qdrant | no r8 write | projection/recall only |
| GitHub Projects | no r8 mutation | workflow surface only |

## Rejected and deferred decisions

The proof uses the real r4 decision contract and attempts to build the real r5
append command. The r5 constructor rejects both outcomes before the history adapter
is called. Consequently they cannot produce a durable approved entry, r6 selection,
laboratory execution or observation claiming approval.

## Non-goals

- no real specialist backend;
- no cross-laboratory execution;
- no new Scheduler, `LaboratoryManager`, queue, registry or EventBus;
- no ProjectV2 operator UI;
- no controlled remote publication;
- no long-term performance learning.
