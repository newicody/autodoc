# Portable specialist contract — 0284-r2

## Decision

Phase 0284-r1 established that the repository already owns the laboratory
framework, deterministic fake provider, existing-Scheduler visit path,
specialist route frames, local handoff, recall closure and real SQL/E5/Qdrant
bindings. The only justified new runtime surface is an immutable description of
a specialist that remains stable while the specialist is declared compatible
with different laboratories.

```text
PortableSpecialistDescriptor
├── stable specialist_ref
├── SpecialistCapabilityContract[]
├── accepted_input_contract_refs[]
├── produced_output_contract_refs[]
├── SpecialistExecutionProfile
└── SpecialistLaboratoryBinding[]
```

```text
portable_specialist_contract_added: true
stable_specialist_identity: true
existing_laboratory_contract_reused: true
existing_specialist_route_frames_reused: true
provider_attached: false
runtime_attached: false
```

## Portability boundary

The same `specialist_ref` can be declared for several laboratory references.
Each binding states the allowed visit modes and the laboratory capabilities
required by the specialist. A binding is compatibility metadata only:
`provider_bound` and `runtime_attached` are immutable false values.

```text
specialist:requirements-analyst
    ├── laboratory:local-fake  [resident, visitor]
    └── laboratory:partner-b   [visitor, transfer]
```

The descriptor does not decide which laboratory is used. A later adapter may
validate a Scheduler route/visit against the descriptor, but Scheduler remains
the sole orchestration authority.

## Existing contracts bridged without imports

`validate_portable_specialist_visit_contract()` validates only the shared
reference vocabulary:

```text
specialist_ref
laboratory_ref
input_contract_ref
output_contract_ref
visit_mode
```

It deliberately does not import or instantiate:

```text
SpecialistDispatchCommand
SpecialistDemandFrame
SpecialistOpinionFrame
LaboratoryVisitRequest
LaboratoryVisitResult
LaboratoryProvider
Scheduler
```

The functional adapter between these existing contracts belongs to a later
patch. This patch is contract-only.

## Execution preferences

`SpecialistExecutionProfile` records bounded preferences for:

- in-process, local-process or remote-service execution;
- deterministic execution;
- maximum parallel visits;
- network and external-call allowance;
- optional accelerator/device references.

A remote-service preference requires an explicit network allowance. An
accelerator requirement requires at least one typed device reference. These are
preferences and limits, not an execution backend.

## Locked architecture

```text
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
new_provider_added: false
new_registry_added: false
new_bus_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
external_dependencies_added: false
```

## Next patch

```text
0284-r3-specialist-laboratory-message-contract
```

That patch may define portable specialist/laboratory conversation messages. It
must still reuse the existing Scheduler and laboratory visit chain.
