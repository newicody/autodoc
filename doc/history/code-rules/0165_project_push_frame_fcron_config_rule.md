# Code rule — 0165 project push frame and fcron config

## Rule

Do not start fcron.

Do not manage OpenRC.

Use ConfigObj-style config as the source of scheduling intent and write only an
idempotent fcron table block for the concerned table. No duplicate fcron entry is
allowed.

## Required behavior

- Use ConfigObj for the operator config surface, with a fallback parser only for
  tests or minimal environments.
- Require `github.token_env`; never store the actual token in config.
- Require one explicit external repository.
- Reject the Autodoc/MissiPy development repository as an artifact source.
- Lock the initial scan interval to 10 minutes.
- Keep the command as scan-once and exit.
- Keep history append-only.
- Treat Copilot opinion as advisory only.
- Copilot opinion is advisory only.
- Use ticket + column name + options as the first artifact payload boundary.

## Forbidden behavior

- Do not create a new GitHub adapter.
- Do not call GitHub API in 0165.
- Do not start fcron.
- Do not run fcrontab commands.
- Do not manage OpenRC.
- Do not write SQL.
- Do not write Qdrant.
- Do not run Scheduler.
- Do not run LLM or OpenVINO.
- Do not use the Autodoc/MissiPy development repository as a business artifact source.

## Reuse

Later phases must continue to reuse existing builders and gates:

- `source_candidate_read_only_external_probe`
- `source_candidate_external_probe_bundle`
- `source_candidate_github_projection_payload`
- `source_candidate_remote_mutation_gate`
- `github_project_scenario`
- `github_publication_review`
