# Changelog 0284-r3 — specialist/laboratory message contract

- Added immutable `SpecialistLaboratoryMessage` and append-only
  `SpecialistLaboratoryConversation` contracts.
- Added pure projections from the existing visit request/result and specialist
  demand/opinion frame vocabulary.
- Preserved `/dev/shm` route frames as the fast local data plane.
- Kept EventBus observation-only and SQL as durable authority.
- Added no provider, handler, transport, registry, Scheduler, SQL, Qdrant,
  OpenVINO or GitHub effect.

```text
message_contract_added: true
existing_route_frames_reused: true
transport_created: false
scheduler_modified: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
```
