# Changelog 0284-r2 — portable specialist contract

- Added immutable `PortableSpecialistDescriptor` with a stable
  `specialist_ref` independent of the current laboratory.
- Added `SpecialistCapabilityContract` for declared capabilities and accepted /
  produced contract references.
- Added `SpecialistExecutionProfile` for bounded execution preferences without
  selecting or instantiating a backend.
- Added `SpecialistLaboratoryBinding` for positive laboratory compatibility and
  resident, visitor or transfer visit modes.
- Added a pure compatibility validator for the shared specialist/laboratory
  route vocabulary.
- Added no provider, handler, registry, worker, Scheduler, EventBus, SQL,
  Qdrant, OpenVINO or GitHub effect.

```text
portable_specialist_contract_added: true
stable_specialist_identity: true
existing_laboratory_contract_reused: true
existing_specialist_route_frames_reused: true
provider_attached: false
runtime_attached: false
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
projects_repository_change_required: false
external_dependencies_added: false
```
