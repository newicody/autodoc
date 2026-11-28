# Laboratory framework reuse audit — 0273-r1

## Purpose

This phase audits the current Autodoc/MissiPy repository before introducing a first-class laboratory boundary for specialists.

A laboratory is an execution framework that may host one or more specialists. The first implementation will be a deterministic local fake. Future providers may wrap GenAI or another external framework. This audit adds no runtime, manager, bus, registry, backend, network path, SQL write, Qdrant projection or GitHub mutation.

## Architectural conclusion

The repository already contains the orchestration, deliberation, transport, persistence, recall, observation and visualization surfaces required around a laboratory.

The laboratory must therefore be introduced as:

```text
versioned laboratory contract
-> capability entry in the existing Scheduler-owned registry
-> Handler-resolved laboratory provider
-> existing specialist and deliberation contracts
-> existing SQL / E5 / Qdrant / EventBus / PassiveSupervisor paths
```

It must not be introduced as a `LaboratoryManager`, `LaboratoryOrchestrator`, `LaboratoryBus`, `LaboratoryScheduler`, parallel registry, parallel context authority or parallel visualization path.

Scheduler remains the orchestration authority. SQL remains the durable authority. Qdrant remains a reconstructible projection and recall index. EventBus remains observation-only. ControlProxy and RouteProxy remain the fast data plane. PassiveSupervisor and Cell Lens remain the read-only observation and visualization path.

## Reuse inventory

### Durable intake and closed vector loop

Reuse without replacement:

- `src/context/github_project_v2_source_candidate_durable_consumer_0272.py`
- `src/context/github_project_v2_source_candidate_vector_projection_0272.py`
- `src/context/github_project_v2_source_candidate_closed_loop_smoke_0272.py`
- `src/context/scheduler_managed_sql_ref_openvino_embedding_usage_0261.py`
- `src/context/scheduler_managed_embedding_qdrant_projection_usage_0262.py`
- `src/context/scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py`

A promoted or merged `SourceCandidate` becomes durable before laboratory selection. Laboratory providers receive typed refs and bounded context, not ownership of SQL or Qdrant. External laboratory embeddings are not inserted into the local E5 space; external text or artifacts are persisted and embedded again through the controlled local profile.

### Specialist-to-kernel boundary

Reuse and extend only through a versioned contract:

- `src/runtime/specialist_kernel_boundary.py`
- `SpecialistKernelCommand`
- `SpecialistKernelBoundaryPlan`

Existing invariant:

```text
SpecialistKernelCommand
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
```

Laboratory identity must not bypass this path. 0273-r2 may add a separate `missipy.laboratory.v1` envelope that references a specialist command, or a new explicitly versioned specialist command. The existing `missipy.specialist.kernel_command.v1` meaning must not change silently.

### Server-oriented deliberation

Reuse without a parallel cycle:

- `src/context/server_oriented_deliberation_cycle.py`
- `ServerOrientation`
- `SpecialistPreliminaryOpinion`
- `RefinedSpecialistDemand`
- `DeliberationRound`
- `SpecialistBusStatistics`
- `FinalArtifactEnvelope`

The laboratory provider executes one bounded visit or mission inside the existing deliberation lifecycle. `ServerOrientation` continues to define axes, requested specialists and expected evidence. `FinalArtifactEnvelope` remains the candidate publication boundary.

### Scheduler deliberation routes

Reuse without a new local orchestrator:

- `src/context/scheduler_deliberation_route_contract.py`
- `DeliberationCycleCommand`
- `DeliberationRoundCommand`
- `SpecialistDispatchCommand`
- `SpecialistDemandFrame`
- `SpecialistOpinionFrame`
- `SchedulerDeliberationRouteBridge`
- `DeliberationObservationFact`

The existing Scheduler remains the deliberation orchestrator. `/dev/shm` deliberation frames remain the multitask data-plane interface. SQL remains the cycle-state authority. EventBus carries facts and references, not specialist payload commands.

### Runtime and component registries

Reuse and extend the current registry model:

- `src/context/prod_server_component_registry_0242.py`
- `src/context/scheduler_owned_runtime_reuse_source_map_0256.py`
- `src/context/scheduler_owned_runtime_registry_0257.py`
- `src/context/scheduler_runtime_bootstrap_registry_attachment_0258.py`

There must be no `LaboratoryRegistry` parallel to the Scheduler-owned registry. A laboratory provider is a declared capability/component entry. Provider construction remains outside the Scheduler core.

### Context variation and retrieval

Reuse:

- `src/context/context_variation_core_contract.py`
- `src/context/context_exploration_planner.py`
- `src/context/sql_context_store.py`
- existing OpenVINO/E5 and Qdrant adapters
- the embedding-space compatibility gate introduced by 0272-r9

A laboratory receives bounded `context_refs` and evidence refs. It may request additional context through a typed specialist command. It does not query SQL or Qdrant directly unless acting behind an explicitly declared adapter invoked by a Handler.

### RouteProxy, ControlProxy and SHM

Reuse the existing route runtime manager and handler surfaces, frame codec, fixed-slot mmap ring, notification primitive, leases, generation table and ControlProxy priority/stale-zone mechanisms.

There is no laboratory-specific bus. The fake laboratory may initially run in-process while producing the same typed visit result. Later providers may use existing route frames and return routes. ControlProxy may apply fast backpressure, but Scheduler policy remains the decision authority.

### Result, observation and visualization

Reuse:

- closed `ResultFrame` surfaces from 0264;
- EventBus observation facts and the 0221-0234 supervision chain;
- PassiveSupervisor cellular snapshot and read model;
- visual layout model and pipeline from 0236-0238;
- renderer-neutral Cell Lens projection;
- VisPy desktop and browser Canvas/SSE renderers.

```text
laboratory/provider activity
-> normalized EventBus facts
-> PassiveSupervisor
-> cellular snapshot
-> visual read model
-> layout
-> VisPy / Canvas / SSE
```

No renderer imports a laboratory framework. No laboratory imports VisPy. Visualization is passive and must not become a policy or fitness authority.

### GitHub exchange and publication

Reuse the ticket/request artifact contracts, Actions artifact fetch-once, attachment fetch, ProjectV2 snapshot/change/gate path, publication review and dry-run/fake adapter surfaces.

The authoritative request artifact and advisory Copilot artifact remain separate. Laboratory results first become local immutable artifacts. Only a reviewed `FinalArtifactEnvelope` may reach a future real GitHub mutation adapter.

## Minimal missing seam

1. `LaboratoryDescriptor`: `laboratory_ref`, provider kind, capabilities, accepted contracts, execution boundary and observation attributes.
2. `LaboratoryVisitRequest`: `visit_ref`, laboratory, specialist, objective, source, cycle, round, bounded context/evidence refs, expected output, return route and resource budget.
3. `LaboratoryVisitResult`: matching refs, immutable status/result, human representation, evidence, assumptions, confidence, follow-up requests and provenance.
4. Provider membrane: a small injectable protocol/callable at the Handler boundary, with no orchestration ownership or implicit backend.
5. Registry capability binding: extend the existing registry/source-map model, with no new registry authority.

## Reserved inter-laboratory identities

The first contract must reserve, without activating network behavior:

- `origin_laboratory_ref`;
- `target_laboratory_ref`;
- `conversation_ref`;
- `parent_visit_ref`;
- `return_route_ref`.

Future specialist dialogue remains mediated:

```text
specialist request
-> typed kernel command
-> Scheduler and policy
-> target laboratory visit
-> immutable result
-> return route
```

## Rejected designs

- a new `LaboratoryManager`;
- a laboratory-owned Scheduler loop;
- a laboratory-owned SQL/Qdrant authority;
- one Qdrant instance or collection per laboratory;
- a new EventBus or visualization bus;
- direct specialist-to-specialist sockets;
- importing GenAI into the kernel;
- changing `Scheduler.run()`;
- using a fake provider as proof of real backend integration;
- injecting external embeddings into the local E5 collection.

## Ordered implementation plan

### 0273-r2 — versioned laboratory contracts

Add immutable, serializable and bounded contracts. Extend the existing registry model only after inspecting its current record type.

```text
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
```

### 0273-r3 — deterministic fake provider and registry binding

Add one stdlib-only fake provider behind the declared Handler/adapter boundary. It executes one bounded visit and returns an immutable result. The fake is a tracer bullet, not a real laboratory validation.

### 0274 — complete local laboratory walking skeleton

```text
durable SourceCandidate
-> ServerOrientation
-> Scheduler deliberation command
-> registered fake laboratory provider
-> specialist opinion / follow-up / validation / synthesis
-> FinalArtifactEnvelope
-> SQL persistence and controlled vector projection
-> EventBus / PassiveSupervisor / Cell Lens
-> GitHub publication preview
```

### 0275 and later

Deploy the two-artifact GitHub Actions path, add the real Copilot advisory producer, close the reviewed return to GitHub, replace the fake with the native Autodoc laboratory, run the Chalouf project, and only then integrate a GenAI or partner laboratory.

## Gates for 0273-r2

Refuse r2 if it adds a second registry, manager, Scheduler or EventBus; changes `Scheduler.run()`; silently modifies a v1 contract; gives a laboratory direct SQL/Qdrant/GitHub/VisPy ownership; omits a bounded resource budget; adds GenAI; treats the fake as a real backend; or creates an unmediated network path.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing rules already cover reuse, kernel convergence, resource bounds and passive observation
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
