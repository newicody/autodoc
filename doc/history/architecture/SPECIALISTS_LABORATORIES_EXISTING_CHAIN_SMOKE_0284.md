# Specialists/laboratories existing-chain smoke — 0284-r5

## Decision

The repository already has a functional fake laboratory closed loop. Phase r5
therefore does not add a specialist runner or a laboratory orchestrator. It
adds a thin composition around the existing smoke:

```text
PortableSpecialistExistingChainSmokeCommand
├── PortableSpecialistDescriptor
├── selected specialist_ref
└── existing FakeLaboratoryClosedLoopSmokeCommand
```

The existing smoke owns the functional execution:

```text
caller-owned running Scheduler
→ PolicyEngine
→ PriorityQueue
→ Scheduler.run
→ Dispatcher
→ LaboratoryVisitRequestHandler
→ deterministic fake laboratory provider
→ durable handoff and recall closure
```

After the existing smoke returns, r5 selects the receipt belonging to the
portable `specialist_ref`. The receipt's existing request/result and the
existing preliminary opinion are projected into:

```text
SpecialistDemandFrame
→ SpecialistLaboratoryMessage(kind=demand)
→ SpecialistOpinionFrame
→ SpecialistLaboratoryMessage(kind=opinion)
→ SpecialistLaboratoryConversation
```

No second execution occurs during this projection.

## Functional status

The fake specialist is functional because the selected specialist traverses the
real existing Scheduler/Handler/provider path and produces an observable closed
result. The backend is still the deterministic fake provider, so the
walking-skeleton status remains transitional rather than claiming a real
specialist backend.

```text
fake_specialist_functional: true
live_path_status: transition
live_path_uses_real_backend: false
```

## Transfer status

The typed r4 transfer boundary is not executed here. Only
`laboratory:local-fake` is registered in the validated runtime; inventing a
second provider solely to make a transfer smoke green would create a false
architecture proof.

```text
transfer_contract_available: true
transfer_execution_performed: false
```

## Locked boundaries

```text
Scheduler = sole orchestrator
EventBus = observation only
SQL = durable authority
Qdrant = projection and recall only
/dev/shm route frames = fast local data plane
ControlProxy = lateral control surface
GitHub = review/publication surface behind a gate
```

```text
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
new_provider_added: false
new_registry_added: false
new_bus_added: false
projects_repository_change_required: false
```
