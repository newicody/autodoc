# Manifest — 0285-r6 Scheduler-approved specialist revision selection

Patch id: `0285-r6-scheduler-approved-specialist-revision-selection`

## Modified

- `src/contracts/event.py`

## Added

- `src/context/scheduler_approved_specialist_revision_selection_0285.py`
- `tests/context/test_scheduler_approved_specialist_revision_selection_0285.py`
- `tests/rules/test_scheduler_approved_specialist_revision_selection_0285_rule.py`
- `PHASE0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_REPORT.md`
- `doc/architecture/SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_0285.md`
- `doc/architecture/SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION_0285.dot`
- `doc/CHANGELOG_0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION.md`
- `doc/manifests/MANIFEST_0285_R6_SCHEDULER_APPROVED_SPECIALIST_REVISION_SELECTION.md`

## Runtime impact

- two enum members appended after all existing `EventType` members;
- one handler available for registration on the existing Dispatcher;
- no automatic registration, dispatch, persistence, projection or remote mutation;
- no dependency outside the Python standard library and existing Autodoc contracts.

## Verification

- contract and rule tests;
- cumulative r2-r6 targeted tests;
- compileall;
- patch whitespace and isolated application checks;
- cumulative Projects `INSTALLATION.md` review.
