# Manifest — 0287-r7-r15-r2-r2

## Added

- `PHASE0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_REPORT.md`
- `doc/CHANGELOG_0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR.md`
- `doc/architecture/PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_0287_R7_R15_R2_R2.md`
- `doc/architecture/PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR_0287_R7_R15_R2_R2.dot`
- `doc/manifests/MANIFEST_0287_R7_R15_R2_R2_PROJECTS_VIEWS_ACTIONS_READINESS_REPAIR.md`
- `templates/github/projects-repository/scripts/projects_bundle_readiness_contract.py`
- `templates/github/projects-repository/scripts/check_projects_bundle_readiness.py`
- `tests/tools/test_projects_bundle_readiness_0287_r7_r15_r2_r2.py`
- `tests/rules/test_projects_bundle_readiness_0287_r7_r15_r2_r2_rule.py`

## Modified

- `templates/github/projects-repository/INSTALLATION.md`

## Boundaries

- query-only GitHub API access;
- no `--execute` surface in the new CLI;
- no ProjectV2, Actions, variable or workflow mutation;
- no Scheduler/laboratory/specialist/runtime changes;
- no external dependency;
- DOT source only, no generated SVG.
