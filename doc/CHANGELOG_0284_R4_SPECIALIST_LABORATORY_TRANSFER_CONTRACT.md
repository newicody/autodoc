# Changelog 0284-r4 — specialist/laboratory transfer contract

- Added immutable `SpecialistTransferRequest`, `SpecialistTransferVisitPlan` and
  `SpecialistTransferResult` contracts.
- Added a pure projection to the existing `LaboratoryVisitRequest` field
  vocabulary.
- Distinguished temporary visits from durable transfers.
- Preserved specialist identity, conversation, parent-visit lineage, context,
  evidence and return route.
- Added no provider, transport, registry, Scheduler, EventBus command, SQL,
  Qdrant, OpenVINO or GitHub effect.

```text
specialist_transfer_contract_added: true
specialist_identity_preserved: true
visit_lineage_preserved: true
transport_created: false
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
```
