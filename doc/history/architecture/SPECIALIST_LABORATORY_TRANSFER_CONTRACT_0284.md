# Specialist/laboratory transfer contract — 0284-r4

## Decision

The existing laboratory contract already supports cross-laboratory visits with
`origin_laboratory_ref`, `target_laboratory_ref`, `conversation_ref` and
`parent_visit_ref`. The visit result already supports requests for another
laboratory. Phase 0284-r4 therefore adds only the portable continuity contract
between an existing result and the next existing visit request.

```text
source LaboratoryVisitResult.requested_laboratory_refs
        ↓ validate target and portable binding
SpecialistTransferRequest
        ↓ pure projection
SpecialistTransferVisitPlan
        ↓ fields for existing LaboratoryVisitRequest
existing Scheduler.emit()
        ↓ existing handler/provider path
SpecialistTransferResult
```

## Visit versus transfer

```text
mode=visit
origin laboratory remains home
completed target visit returns active_laboratory_ref to origin

mode=transfer
identity remains stable
completed target visit sets active_laboratory_ref to target
```

Both modes preserve:

```text
specialist_ref
conversation_ref
source_visit_ref → parent_visit_ref
context_refs
evidence_refs
return_route_ref
```

## Existing boundaries

The visit plan does not instantiate `LaboratoryVisitRequest`; it exposes the
validated fields needed by the existing contract. The next patch may compose
that plan with the existing Scheduler path, but direct provider calls remain
forbidden.

```text
Scheduler                    = sole orchestrator
/dev/shm route frames         = fast local data plane
EventBus                     = observation only
SQL                          = durable authority
Qdrant                       = projection and recall only
transfer contract            = immutable plan/result, no transport
```

```text
specialist_transfer_contract_added: true
specialist_identity_preserved: true
visit_lineage_preserved: true
transport_created: false
runtime_attached: false
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
