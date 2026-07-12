# Changelog — 0275-r6 GitHub research Kanban operator model

## Added

- canonical human-facing Project model;
- optional `Thème` swimlanes containing multiple durable research tickets;
- `Étape` columns: Recherche, En cours, Terminé, Développement, Production,
  Drop;
- same-ticket cycle history semantics;
- related-research, media and external-inference intentions;
- next-cycle context exclusion semantics;
- preparatory GitHub Project installation and cleanup runbook;
- executable rule tests for the locked model.

## Boundaries

- documentation and tests only;
- no runtime or network access;
- no Scheduler or `Scheduler.run()` modification;
- no GitHub mutation;
- no OpenRC service;
- no external dependency.
