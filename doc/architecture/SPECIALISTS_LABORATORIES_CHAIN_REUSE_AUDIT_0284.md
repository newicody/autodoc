# Specialists/laboratories chain reuse audit — 0284-r1

## Conclusion

The repository already contains the laboratory execution chain. Phase 0284
must extend it rather than create another framework or orchestrator.

```text
architecture_preserved: true
existing_laboratory_contract_reused: true
existing_fake_provider_reused: true
existing_scheduler_visit_binding_reused: true
existing_specialist_route_frames_reused: true
existing_handoff_recall_smoke_reused: true
existing_qdrant_chain_reused: true
```

## Existing chain

```text
LaboratoryDescriptor / LaboratoryVisitRequest / LaboratoryVisitResult
→ deterministic local fake provider membrane
→ existing Scheduler.emit / PolicyEngine / PriorityQueue / Scheduler.run
→ existing Dispatcher and LaboratoryVisitRequestHandler
→ fake multi-specialist deliberation
→ SQL handoff + observation-only EventBus facts
→ recall and closed ResultFrame
→ existing-Scheduler closed-loop smoke
→ GitHub dual-artifact and operator-advisory bridges
```

The real 0283 SQL/E5/Qdrant projection and recall bindings are also reusable by
later laboratory workflows. They are not moved into a laboratory-owned
database or vector authority.

## Existing specialist route layer

The existing deliberation route contract already provides:

```text
SpecialistDispatchCommand
SpecialistDemandFrame
SpecialistOpinionFrame
SchedulerDeliberationRouteBridge
/dev/shm route paths
```

These frames remain the fast local route plane. They are not replaced by
EventBus or a new message broker.

## Required references already preserved

```text
laboratory_ref
origin_laboratory_ref
target_laboratory_ref
visit_ref
specialist_ref
conversation_ref
context_refs
return_route_ref
```

The visit result can already request additional context, specialists and
laboratories.

## Actual missing contract

There is no first-class portable specialist descriptor/profile that can be
bound to different laboratories while reusing both:

```text
existing specialist dispatch/demand/opinion frames
existing laboratory visit request/result contracts
```

```text
portable_specialist_contract_missing: true
```

A new generic laboratory framework, fake provider, Scheduler, registry,
EventBus, route plane or runtime manager is not justified.

## Locked boundaries

```text
new_laboratory_manager_justified: false
new_scheduler_justified: false
scheduler_modified: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_fast_route_plane: true
control_proxy_lateral_only: true
projects_repository_change_required: false
external_dependencies_added: false
```

## Next patch

```text
0284-r2-portable-specialist-contract
```

It must add immutable portable-specialist contracts only. It must not attach a
new provider or alter `Scheduler.run`.
