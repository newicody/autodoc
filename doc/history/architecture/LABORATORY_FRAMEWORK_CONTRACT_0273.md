# Laboratory framework contract — 0273-r2

## Purpose

0273-r2 adds the first versioned laboratory vocabulary while keeping every
runtime boundary closed.

A laboratory is a framework capable of executing a bounded specialist visit.
The first provider will be a deterministic fake in 0273-r3. Later providers may
wrap the native Autodoc laboratory, GenAI, or a partner framework.

This phase adds no provider and performs no visit.

## Contracts

### LaboratoryDescriptor

Declares:

- stable `laboratory_ref`;
- provider kind;
- capabilities;
- accepted input contract refs;
- produced output contract refs;
- execution boundary;
- availability and explicit enablement;
- network permission;
- metadata.

A descriptor is not a provider instance.

### LaboratoryResourceBudget

Bounds every visit:

- duration;
- output characters;
- context references;
- evidence references;
- follow-up requests;
- specialist messages;
- external calls;
- network permission.

Network is denied by default. A non-network budget cannot reserve external
calls.

### LaboratoryVisitRequest

Carries:

- `visit_ref`;
- `laboratory_ref`;
- `specialist_ref`;
- objective and source candidate refs;
- context generation;
- input and output contract refs;
- bounded context/evidence refs;
- return route;
- resource budget.

Its next boundary is always `Scheduler.emit()`. It does not grant direct access
to SQL, Qdrant, GitHub, EventBus, RouteProxy, ControlProxy, VisPy or a provider
backend.

### LaboratoryVisitResult

Carries:

- matching visit/laboratory/specialist refs;
- typed status;
- output contract ref;
- deeply frozen JSON-compatible machine result;
- human representation;
- confidence;
- evidence and assumptions;
- context, specialist, laboratory and follow-up requests;
- provenance.

A result is local and non-publishable by default. EventBus cannot be used as
its command path.

## Inter-laboratory reservation

The v1 contracts reserve:

- `origin_laboratory_ref`;
- `target_laboratory_ref`;
- `conversation_ref`;
- `parent_visit_ref`;
- `return_route_ref`.

No network behavior is implemented. A cross-laboratory request requires an
explicit conversation ref. A request to another laboratory is rejected during
result validation unless the originating visit budget explicitly permits
network use.

The future path remains mediated:

```text
specialist result/request
-> Scheduler.emit()
-> PolicyEngine
-> Queue
-> Dispatcher
-> Handler
-> target laboratory provider
-> immutable result
-> return route
```

## Existing registry binding

`LaboratoryRegistryBindingPlan` targets:

```text
context.scheduler_owned_runtime_registry_0257
SchedulerOwnedRuntimeComponentRegistration
```

It does not create another registry and does not mutate the existing one.

For 0273-r2:

```text
provider_active = false
ready_for_registry_attachment = false
provider_source_paths = []
owner = scheduler
role = command
```

0273-r3 may populate a real source path for the deterministic fake provider and
convert the validated plan into the existing registration type.

## Authority boundaries

- Scheduler remains orchestration authority.
- SQL remains durable authority.
- E5/OpenVINO remains embedding-only.
- Qdrant remains projection/recall by `sql_ref`.
- EventBus remains observation-only.
- PassiveSupervisor and VisPy remain passive readers.
- ControlProxy and RouteProxy remain data-plane surfaces.
- GitHub remains artifact workflow and reviewed publication surface.

The contract module imports none of those backends.

## Rejected behavior

- modifying `Scheduler.run()`;
- adding a LaboratoryManager, LaboratoryScheduler or LaboratoryBus;
- attaching a provider in r2;
- direct SQL/Qdrant/GitHub/VisPy access;
- implicit network access;
- peer-to-peer specialist sockets;
- injecting external embeddings into the local E5 space;
- claiming the future fake provider as a real backend.

## Next phase

0273-r3 will add one deterministic stdlib-only fake provider and bind it through
the existing Scheduler-owned registry record. It will execute one bounded visit
without network, SQL/Qdrant ownership, GitHub mutation, EventBus command use or
VisPy imports.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.laboratory.v1
context_contract_changed: true
external_dependencies_added: false
scheduler_modified: false
provider_active: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
