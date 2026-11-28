# Changelog 0284-r1 — specialists/laboratories chain reuse audit

- Added a source-only audit of the existing laboratory and specialist route
  surfaces.
- Confirmed reuse of the 0273 laboratory contracts and fake provider.
- Confirmed reuse of the 0274 existing-Scheduler visit, deliberation, handoff,
  recall and smoke chain.
- Confirmed reuse of the 0275/0281 GitHub laboratory bridges.
- Confirmed reuse of the 0283 real SQL/E5/Qdrant chain.
- Identified the missing first-class portable specialist contract.
- Rejected a LaboratoryManager, second Scheduler, second route plane or
  laboratory-owned persistence authority.

```text
architecture_preserved: true
existing_laboratory_contract_reused: true
existing_fake_provider_reused: true
existing_scheduler_visit_binding_reused: true
existing_specialist_route_frames_reused: true
existing_handoff_recall_smoke_reused: true
existing_qdrant_chain_reused: true
portable_specialist_contract_missing: true
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
