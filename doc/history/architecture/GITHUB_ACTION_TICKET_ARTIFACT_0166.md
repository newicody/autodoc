# 0166 — GitHub Action ticket artifact contract

## Decision

0166 adds the external GitHub Action ticket-artifact contract and templates.

The external idea repository creates artifacts immediately when an issue/ticket is
created or edited. The local Autodoc server still polls later through the 0165
fcron scan-once contract.

## Artifact boundary

The first artifact carries only:

```text
ticket + column name + options
```

The column name is taken from the ticket/issue form body in this phase. 0166 does
not read GitHub API or ProjectV2 fields.

It does not read GitHub API.

## Copilot preliminary opinion

Copilot preliminary opinion is advisory only. It is modeled as an artifact
sibling under the same project push frame.

Copilot preliminary opinion is an artifact sibling. The local server can later accept it
as a hint only if local validation judges it receivable.

## Reuse

0166 must reuse 0165 ProjectPushFrame concepts:

- origin frame id
- ticket revision id
- context options
- Copilot advisory-only validation

It does not create a scheduler, a SQL writer, a Qdrant writer, or a GitHub API
client.

## Templates

0166 includes templates for the external idea repository:

- GitHub Action workflow
- standalone artifact builder script
- issue form

These templates are intended to be copied into the external idea repository.
They are not activated inside the Autodoc development repository.

## Boundary

- external idea repository produces artifacts
- local server polls later
- no GitHub API call in 0166
- no remote mutation
- no fcron/OpenRC change
- no SQL/qdrant write
- no inference execution
