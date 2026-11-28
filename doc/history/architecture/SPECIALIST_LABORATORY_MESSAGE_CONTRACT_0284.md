# Specialist/laboratory message contract — 0284-r3

## Decision

The repository already owns two operational vocabularies:

```text
Scheduler route vocabulary
SpecialistDispatchCommand
SpecialistDemandFrame
SpecialistOpinionFrame

Laboratory visit vocabulary
LaboratoryVisitRequest
LaboratoryVisitResult
```

Phase 0284-r3 does not replace either vocabulary. It supplies the missing
portable conversation envelope joining them around the stable
`specialist_ref` introduced in 0284-r2.

```text
PortableSpecialistDescriptor
        ↓ compatibility validation
LaboratoryVisitRequest
        +
SpecialistDemandFrame
        ↓ pure projection
SpecialistLaboratoryMessage(kind=demand)
        ↓ reply link
SpecialistLaboratoryMessage(kind=opinion)
        ↑ pure projection
SpecialistOpinionFrame
        +
LaboratoryVisitResult
```

## Message identity and continuity

A message carries:

```text
message_ref
conversation_ref
visit_ref
sequence_no
specialist_ref
origin_laboratory_ref
target_laboratory_ref
sender_ref
recipient_ref
contract_ref
return_route_ref
route_ref
route_frame_ref
reply_to_message_ref
context_refs
evidence_refs
observation_fact_refs
```

A conversation is immutable and append-only. Sequence numbers are contiguous
from zero and every non-root message replies to an earlier message.

## Existing planes remain authoritative

```text
/dev/shm route frames = fast local data plane
Scheduler             = sole orchestration authority
SQL                   = durable authority
Qdrant                = projection and recall only
EventBus               = observation only
message contract       = immutable envelope, no transport
```

The payload is frozen JSON data. The contract performs no I/O and creates no
queue, worker, manager, provider, registry or bus.

## Locked boundaries

```text
message_contract_added: true
existing_route_frames_reused: true
transport_created: false
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
```
