# Changelog — 0275-r9 GitHub results/updates interface lock

## Added

- simplified research form;
- append-only result-update form;
- result/update presentation contract;
- final Results, Server actions, History, Groups and All view model;
- accessibility guidance;
- installation runbook and focused rule tests.

## Changed

- theme form becomes a source-only context group form;
- research parent and related results are explicitly separated;
- repository revision/path selection is explicit;
- current results alone are visible in the main Board;
- r7/r8 rule expectations follow the final interface.

## Removed

- redundant transversal-event issue form.

## Boundaries

- no runtime module;
- no workflow change;
- no Project or issue mutation;
- no Scheduler change;
- no SQL/Qdrant write;
- no non-stdlib dependency.
