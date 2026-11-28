# Changelog — 0287-r7-r15-r2-r2

## Added

- pure ProjectV2 field/view and Actions readiness comparison contract;
- read-only `check_projects_bundle_readiness.py` CLI;
- exact field option, view layout/filter/visible-field/grouping checks;
- selected-Actions, SHA pinning, workflow state and Copilot readiness checks;
- separate `authoritative_ready`, `copilot_ready` and `full_ready` statuses;
- tests, architecture source, report and manifest.

## Changed

- cumulative Projects installation guide now extracts and confirms the actual
  reconciliation digest instead of using a placeholder;
- guide now documents selected-Actions inspection and exact readback;
- Copilot disabled is treated as an optional-path warning, not an authoritative
  workflow failure.

## Unchanged

- ProjectV2 mutation remains owned by the existing controlled reconciler;
- Scheduler, laboratory, specialists, SQL, OpenVINO and Qdrant are unchanged;
- no new dependency or generated SVG is versioned.
