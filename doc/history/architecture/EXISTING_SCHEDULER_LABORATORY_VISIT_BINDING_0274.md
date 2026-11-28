# Existing Scheduler laboratory visit binding — 0274-r1

## Purpose

0274-r1 closes the first live micro-kernel path from a typed laboratory visit
request to the deterministic fake provider.

There is **one existing Scheduler** for the complete platform.
Scheduler.run() is unchanged.

```text
LaboratoryVisitRequest
-> Scheduler.emit()
-> PolicyEngine.decide()
-> existing PriorityQueue
-> existing Scheduler.run()
-> existing Dispatcher
-> LaboratoryVisitRequestHandler
-> DeterministicFakeLaboratoryProvider
-> LaboratorySchedulerVisitReceipt
```

No LaboratoryScheduler, LaboratoryManager, laboratory queue, parallel
EventBus, parallel registry or second orchestration loop is introduced.

## Event contract

The kernel `EventType` receives two explicit values:

```text
LABORATORY_VISIT_REQUEST
LABORATORY_VISIT_RESULT
```

Only the request event is active in 0274-r1. The result enum is reserved for a
later normalized observation boundary. The Handler returns its immutable
receipt through the existing `Request.reply` future.

The Handler does not publish a result event itself. EventBus remains
observation-only: the existing Dispatcher publishes the command event copy for
observers before invoking the Handler.

## Existing Scheduler lifecycle

`submit_laboratory_visit()` accepts `SchedulerContract`. It:

1. builds an immutable `LABORATORY_VISIT_REQUEST`;
2. adds the existing `Request.reply` future;
3. calls `await scheduler.emit(event)`;
4. waits for the Dispatcher/Handler reply;
5. validates the typed receipt.

It never:

- constructs a Scheduler;
- starts `Scheduler.run()`;
- stops the Scheduler;
- constructs a PriorityQueue;
- constructs an EventBus;
- constructs a registry;
- modifies Scheduler policy.

The normal platform bootstrap remains the owner of the one Scheduler lifecycle.
A submission made without the existing Scheduler running times out explicitly.

## Handler boundary

`LaboratoryVisitRequestHandler` is intentionally small. It validates the event
type, destination and payload, then delegates to the r3 provider membrane.

```text
Dispatcher
-> LaboratoryVisitRequestHandler.handle(event)
-> execute_deterministic_fake_laboratory_visit()
-> LaboratoryProvider.execute()
```

The provider still owns no orchestration, persistence, vector index, GitHub
mutation, EventBus command publication, SHM lifecycle or renderer.

## Result receipt

`LaboratorySchedulerVisitReceipt` records:

- event and correlation identities;
- visit and provider refs;
- existing registration component id;
- immutable r3 execution record;
- canonical Scheduler path;
- explicit negative ownership flags.

It requires:

```text
existing_scheduler_used = true
scheduler_created = false
scheduler_run_modified = false
parallel_queue_created = false
parallel_eventbus_created = false
parallel_registry_created = false
result_event_published = false
```

## Relation to deliberation

0274-r1 proves only the live Scheduler-to-provider visit.

0274-r2 will compose the existing deliberation contracts without a new
orchestrator:

```text
durable SourceCandidate
-> ServerOrientation
-> DeliberationCycleCommand / SpecialistDispatchCommand
-> existing Scheduler visit path
-> preliminary opinion or follow-up
-> RefinedSpecialistDemand
-> DeliberationRound
-> liaison / validation / synthesis
-> FinalArtifactEnvelope
```

Later 0274 work will persist the final local artifacts, use the controlled
E5/Qdrant path, emit normalized observation facts, feed PassiveSupervisor and
Cell Lens, and build a GitHub publication preview.

EventBus remains observation-only. PassiveSupervisor remains passive. VisPy remains passive and imports no laboratory provider.

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
scheduler_run_modified: false
parallel_queue_created: false
parallel_eventbus_created: false
parallel_registry_created: false
provider_active: true
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
