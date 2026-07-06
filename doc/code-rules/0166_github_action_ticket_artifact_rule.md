# Code rule — 0166 GitHub Action ticket artifact

## Rule

Ticket artifact carries only ticket + column name + options.

Copilot preliminary opinion is advisory only.

Reuse 0165 ProjectPushFrame concepts and do not create a parallel scheduler or
GitHub adapter.

## Required behavior

- Reuse 0165 ProjectPushFrame, context options, ticket revision and Copilot
  advisory-only validation.
- Keep the artifact producer in the external idea repository.
- Keep the local server as later fcron scan-once consumer.
- Keep Copilot preliminary opinion as a sibling artifact, not authority.
- Keep history append-only in later intake phases.

## Forbidden behavior

- Do not create a new scheduler.
- Do not call GitHub API.
- Do not perform remote mutation.
- Do not write SQL.
- Do not write Qdrant.
- Do not start or edit fcron.
- Do not manage OpenRC.
- Do not run inference.
- Do not use the Autodoc development repository as the business artifact source.
