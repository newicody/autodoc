# Manifest — 0285-r7 specialist capability growth observation projection

Patch id: `0285-r7-specialist-capability-growth-observation-projection`

## Added

- `src/context/specialist_capability_growth_observation_projection_0285.py`
- `tests/context/test_specialist_capability_growth_observation_projection_0285.py`
- `tests/rules/test_specialist_capability_growth_observation_projection_0285_rule.py`
- `PHASE0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_REPORT.md`
- `doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_0285.md`
- `doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION_0285.dot`
- `doc/CHANGELOG_0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION.md`
- `doc/manifests/MANIFEST_0285_R7_SPECIALIST_CAPABILITY_GROWTH_OBSERVATION_PROJECTION.md`

## Existing surfaces reused

- `contracts.event.Event`;
- `EventType.SPECIALIST_REVISION_SELECTION_RESULT`;
- `kernel.event_bus.EventBus.publish` structural boundary;
- r6 approved revision selection result;
- PassiveSupervisor and Cell Lens observation patterns.

## Runtime impact

- one optional passive EventBus publication when called;
- no Scheduler change;
- no SQL/Qdrant/OpenVINO access;
- no laboratory dispatch;
- no GitHub mutation.

## Projects deployment

`INSTALLATION.md reviewed and unchanged` because no `newicody/projects` deployable
surface changes in this phase.
