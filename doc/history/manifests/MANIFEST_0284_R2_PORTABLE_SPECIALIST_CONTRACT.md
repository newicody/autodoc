# Manifest 0284-r2 — portable specialist contract

## Added files

```text
src/context/portable_specialist_contract_0284.py
tests/context/test_portable_specialist_contract_0284.py
tests/rules/test_portable_specialist_contract_0284_rule.py
doc/architecture/PORTABLE_SPECIALIST_CONTRACT_0284.md
doc/architecture/PORTABLE_SPECIALIST_CONTRACT_0284.dot
doc/CHANGELOG_0284_R2_PORTABLE_SPECIALIST_CONTRACT.md
doc/manifests/MANIFEST_0284_R2_PORTABLE_SPECIALIST_CONTRACT.md
PHASE0284_R2_PORTABLE_SPECIALIST_CONTRACT_REPORT.md
```

## Reuse and authority statement

```text
portable_specialist_contract_added: true
stable_specialist_identity: true
existing_laboratory_contract_reused: true
existing_specialist_route_frames_reused: true
existing_scheduler_remains_orchestrator: true
provider_attached: false
runtime_attached: false
scheduler_modified: false
new_scheduler_added: false
new_laboratory_manager_added: false
new_provider_added: false
new_registry_added: false
new_bus_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
projects_repository_change_required: false
external_dependencies_added: false
```

The new module is justified by the explicit missing-contract finding from
0284-r1. It is effect-free and uses only the Python standard library.
