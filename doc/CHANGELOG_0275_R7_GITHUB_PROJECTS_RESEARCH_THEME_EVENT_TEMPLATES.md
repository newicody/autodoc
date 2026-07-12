# Changelog — 0275-r7 GitHub Projects research/theme/event templates

## Added

- installable `Nouvelle recherche` issue form;
- installable theme-container issue form;
- installable independent transversal-event issue form;
- controlled read-only `workflow_dispatch` workflow;
- stdlib helper building an issue-shaped dispatch event;
- Project Board template using the default `Status` field and optional `Thème`;
- installation runbook for `newicody/projects`;
- focused tool and rule tests.

## Changed

- 0275-r6 documentation and rule expectations now use the operator-selected
  default GitHub field name `Status` instead of `Étape`.

## Boundaries

- no watcher;
- no automatic Project transition handling;
- no GitHub write permission;
- no OpenRC service;
- no Scheduler modification;
- no non-stdlib dependency.
