# Deterministic fake laboratory provider — 0273-r3

## Purpose

0273-r3 activates the first `missipy.laboratory.v1` provider as a local,
deterministic tracer bullet. It validates the provider membrane and the
existing Scheduler-owned registry binding before a native Autodoc, GenAI or
partner laboratory is integrated.

The fake provider is not a real laboratory backend.

## Reused boundaries

```text
LaboratoryVisitRequest
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> LaboratoryProvider.execute
-> LaboratoryVisitResult
```

This patch implements only the Handler-side provider membrane and registry
registration. The complete Scheduler walking skeleton is deferred to 0274.
`Scheduler.run()` is not modified.

## Existing registry binding

The provider is represented by the existing
`SchedulerOwnedRuntimeComponentRegistration` type:

```text
component_id = laboratory_provider_local_fake
surface = laboratory_provider
owner = scheduler
role = command
runtime_api_kind = scheduler_owned_object
selected_from_existing_surfaces = false
```

`selected_from_existing_surfaces = false` is deliberate: 0273-r1 proved the
new seam was missing before this provider was added. No parallel registry is
created. The immutable 0257 registry value is copied with one extra
registration, and exact replay is idempotent.

## Provider behavior

The fake provider:

- executes in process;
- uses only the standard library;
- is deterministic for the same visit request;
- refuses network-enabled budgets and external calls;
- accepts only declared input/output contracts;
- returns immutable `LaboratoryVisitResult` records;
- validates every result against the request budget;
- supports deterministic `completed`, `needs_context`, `needs_specialist`,
  `rejected` and `failed` scenarios.

The scenario is selected only through test/operator metadata
`fake_scenario`. No model or heuristic decides it.

## Authority boundaries

The provider does not own:

- Scheduler or policy;
- SQL persistence;
- OpenVINO/E5 embedding;
- Qdrant indexing or recall;
- GitHub mutation;
- EventBus command publication;
- RouteProxy/ControlProxy lifecycle;
- PassiveSupervisor;
- Cell Lens or VisPy.

Future 0274 composition may publish normalized observation facts after the
result crosses the existing result boundary. EventBus remains observation-only,
and VisPy remains a passive renderer.

## Inter-laboratory behavior

No external visit is executed. The v1 contracts keep the reserved laboratory
and conversation refs, but this fake refuses a network-enabled visit. A future
external request must return to `Scheduler.emit()` and pass policy before a
target provider can be invoked.

## Next phase

0274 will compose:

```text
durable SourceCandidate
-> ServerOrientation
-> Scheduler deliberation command
-> registered fake laboratory provider
-> deterministic specialist result/follow-up
-> validation and synthesis
-> FinalArtifactEnvelope
-> persistence / projection / observation / publication preview
```

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
provider_active: true
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
