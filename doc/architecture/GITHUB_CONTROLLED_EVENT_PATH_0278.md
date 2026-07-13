# GitHub controlled event path — 0278

## Problem

GitHub Actions reserves the `GITHUB_*` environment namespace. A workflow step
cannot replace `GITHUB_EVENT_PATH` with a synthetic event path. During a
`workflow_dispatch` run, the authoritative request builder therefore reads the
native dispatch payload, which does not expose an `issue` object.

## Decision

Controlled workflows pass their normalized synthetic Issue event through
`AUTODOC_EVENT_PATH`. The authoritative request builder prefers that explicit
path and falls back to GitHub's native `GITHUB_EVENT_PATH` for workflows
triggered directly by an Issue event.

## Boundaries

- the normalized Issue event remains local to the runner;
- no Issue or ProjectV2 mutation is introduced;
- no SQL or Qdrant write is introduced;
- Scheduler and `Scheduler.run()` are unchanged;
- no non-stdlib dependency is introduced.
