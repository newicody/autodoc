# Manifest 0287-r7-r15-r3-r16-r2-r2

## Modified

- Projects bundle drift contract;
- Projects bundle ownership manifest;
- bundle README;
- drift-audit runbook;
- focused drift-audit functional tests.

## Added

- transient-boundary architecture rule;
- phase report;
- changelog;
- architecture note and DOT graph;
- changed-files manifest.

## Locked boundaries

- only `__pycache__`, `.pyc` and `.pyo` are ignored;
- ignored files remain visible in a dedicated result field;
- unknown non-transient files still require review;
- no mutation, network access or delete candidate is introduced.
