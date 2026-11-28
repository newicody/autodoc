# GitHub Copilot advisory optionality — 0277

## Decision

The GitHub Issue request artifact remains authoritative. A Copilot artifact is
an optional, untrusted hint. Copilot unavailability must not prevent creation
and upload of the authoritative request and linking manifest.

## Authentication

Versioned workflows use the ephemeral GitHub Actions `GITHUB_TOKEN` with the
scoped `copilot-requests: write` permission. No durable Copilot token is
required by default.

The `newicody/projects` repository variable
`AUTODOC_COPILOT_ADVISORY_ENABLED` controls installation and execution of the
CLI.

## Failure semantics

The advisory script removes a stale advisory before every attempt. A missing
command, timeout, non-zero CLI exit status, or invalid response creates no
advisory file and returns success by default. Set
`AUTODOC_COPILOT_REQUIRED=true` only for a diagnostic gate.

CLI stderr and token values are never copied into an artifact.

## Authoritative request boundary

The builder now requires a real repository, positive Issue number, and title.
It no longer invents an `Untitled GitHub request` when a workflow event is
misconfigured. An Issue body may legitimately be empty.

## Locked boundaries

- no Issue or ProjectV2 mutation;
- no SQL or Qdrant write;
- no Scheduler or `Scheduler.run()` modification;
- no non-stdlib dependency;
- Copilot output remains `trusted=false` and `usable_as_authority=false`.
