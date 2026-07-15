# Changelog 0287-r7-r7

## Added

- `missipy.research.correlated_work_package.v1`;
- strict correlation of run assembly, intake, Issue attachments and fetch report;
- deterministic work-package identity;
- portable attachment references without bytes or local paths;
- context and rule tests;
- architecture, manifest and phase report.

## Preserved

- request artifact as the only authoritative GitHub content;
- Copilot v1/v2 as hint-only;
- existing fetch and intake modules;
- Scheduler as the only orchestration authority;
- no SQL, Qdrant, GitHub or ProjectV2 mutation.

## Documentation

`doc/README_CURRENT.md` records r7 closure. `INSTALLATION.md` is unchanged
because this phase adds no deployment, workflow, secret or service setting.
