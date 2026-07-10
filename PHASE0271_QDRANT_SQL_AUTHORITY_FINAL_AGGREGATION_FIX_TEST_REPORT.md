# Phase 0271-r6 test report

## Defect reproduced

The 0269 final result reported:

```text
0262 and 0263 must both report sql_authority_ref
```

while both child reports contained the same value. The CLI `_load_report`
allow-list omitted `sql_authority_ref`, so both phase outcomes lost the value
before the core equality gate.

## Correction

- add `sql_authority_ref` to the report-loader allow-list;
- show it in the summary;
- keep the core phase-local equality gate unchanged.

## Targeted validation

```text
pytest targeted: 14 passed
network used: no
Qdrant called: no
SQL written: no
SHM touched: no
```
