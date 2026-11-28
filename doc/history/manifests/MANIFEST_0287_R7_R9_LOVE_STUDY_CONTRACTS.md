# Manifest — 0287-r7-r9 love-study contracts

## Added files

- `src/context/love_study_contracts_0287.py`
- `tests/context/test_love_study_contracts_0287_r7_r9.py`
- `tests/rules/test_love_study_contracts_0287_r7_r9_rule.py`
- `PHASE0287_R7_R9_LOVE_STUDY_CONTRACTS_REPORT.md`
- `doc/architecture/LOVE_STUDY_CONTRACTS_0287_R7_R9.md`
- `doc/architecture/LOVE_STUDY_CONTRACTS_0287_R7_R9.dot`
- `doc/CHANGELOG_0287_R7_R9_LOVE_STUDY_CONTRACTS.md`
- `doc/manifests/MANIFEST_0287_R7_R9_LOVE_STUDY_CONTRACTS.md`

## Modified files

- `doc/README_CURRENT.md`

## Boundaries

- Scheduler remains the only orchestration authority.
- SQL remains the durable context authority.
- Qdrant remains projection and recall only.
- OpenVINO is reused and not reimplemented.
- ControlProxy remains transport-only.
- No runtime is attached in r9.
- Global synthesis remains a later liaison step.
- `INSTALLATION.md` is unchanged because deployment is unchanged.
