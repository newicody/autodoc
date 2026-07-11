# Fake laboratory deliberation composition — 0274-r2

## Purpose

0274-r2 composes the existing laboratory visit path with the existing
server-oriented deliberation and specialist liaison contracts.

There is **one existing Scheduler** for the platform:

```text
ServerOrientation
-> LaboratoryVisitRequest per requested specialist
-> Scheduler.emit()
-> existing PolicyEngine and PriorityQueue
-> existing Scheduler.run()
-> existing Dispatcher and Handler
-> deterministic fake provider
-> SpecialistPreliminaryOpinion
-> RefinedSpecialistDemand when follow-up is required
-> DeliberationRound
-> SpecialistLiaisonSynthesis
-> FinalSynthesisPacket
-> FinalArtifactEnvelope
```

No new Scheduler, local Scheduler loop, laboratory orchestrator, queue, EventBus
or registry is introduced.

## Deliberation behavior

One bounded visit is submitted for every specialist already requested by
`ServerOrientation`.

The deterministic fake result is converted into:

- a preliminary opinion;
- a normalized specialist output fragment;
- a bus observation reference;
- a refined demand only when the fake reports `needs_context`,
  `needs_specialist` or another refinement stance.

Completed visits do not create artificial follow-up demands. If every visit is
completed, the round reaches `ready_for_final_synthesis` and local final
artifacts are built.

A rejected or incomplete cycle remains local and does not produce a final
artifact.

## Publication meaning

`publication_ready = true` means only that local liaison and synthesis are
complete. It does not authorize a remote mutation.

Every result states:

```text
publication_gate_required = true
github_mutation_performed = false
```

The existing GitHub publication review and publication gate remain required.

## Authority boundaries

- the existing Scheduler owns orchestration;
- the fake provider owns only one bounded call;
- SQL remains durable authority but is not written in r2;
- Qdrant remains projection/recall but is not called in r2;
- EventBus remains observation-only;
- PassiveSupervisor and VisPy remain passive;
- GitHub receives no mutation;
- ControlProxy and RouteProxy remain unchanged.

## Determinism

The fake visit requests, opinions, fragments, round, synthesis and final
artifact are derived from stable refs and content. Scheduler event ids are
runtime identities and are not used to define the semantic result.

## Next phase

0274-r3 will close persistence and observation around this local result:

```text
FakeLaboratoryDeliberationResult
-> controlled SQL persistence
-> local E5/Qdrant projection by sql_ref
-> normalized EventBus facts
-> PassiveSupervisor
-> Cell Lens / VisPy
-> GitHub publication preview
```

It will still use the same Scheduler and will not perform a GitHub mutation.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_created: false
scheduler_modified: false
scheduler_run_owned: false
parallel_orchestrator_created: false
parallel_queue_created: false
parallel_eventbus_created: false
parallel_registry_created: false
provider_active: true
sql_write_performed: false
qdrant_projection_performed: false
github_mutation_performed: false
network_added: false
```
