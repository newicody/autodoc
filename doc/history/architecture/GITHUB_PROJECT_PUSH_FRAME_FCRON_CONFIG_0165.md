# 0165 — Project push frame and fcron ConfigObj contract

## Decision

0165 locks the corrected model:

```text
ticket push / ticket move
-> GitHub Action immediately creates artifacts
-> local server is called by fcron every 10 minutes
-> local scan-once downloads/processes new artifacts later
```

Autodoc does not start fcron. Autodoc does not manage OpenRC. The operator edits
the concerned fcron table through an idempotent text update without duplicates.

## Scope

0165 adds contracts and a config check only. It does not call GitHub.

The config is ConfigObj-style and describes:

- external project URL
- external repository
- ticket artifact workflow
- artifact name prefix
- fcron interval
- fcron table path
- token environment variable name
- context options attached to tickets
- Copilot preliminary opinion policy
- append-only history

## Ticket artifact payload

The GitHub Action artifact stays minimal:

```text
ticket + column name + options
```

Options are intent flags, not already-expanded context:

- include current ticket
- include total project
- include repository context
- include linked tickets
- include recent artifacts

## Copilot artifact

Copilot preliminary opinion is advisory only. It may be attached as an additional
artifact under the same project push frame. The local server may use it as a hint
only if local validation judges it receivable.

It is never authority.

## Artifact family

A project push frame groups:

- ticket snapshots
- column/status revisions
- Copilot preliminary opinions
- local inference responses
- user decisions: keep, detach, delete/tombstone, lock, rate, supersede

History is append-only. Changes create new artifacts/revisions instead of
silently mutating older artifacts.

## fcron

The fcron entry is rendered from ConfigObj config and inserted between stable
markers. Re-running the tool updates the same block and avoids duplicates.

The tool does not install the table into the system fcrontab command. It writes
only the configured table file when explicitly called with `--write-fcrontab`.

## Reuse

0165 does not create a new GitHub adapter. Later phases must continue to reuse existing builders:

- source_candidate_read_only_external_probe
- source_candidate_external_probe_bundle
- source_candidate_github_projection_payload
- source_candidate_remote_mutation_gate
- github_project_scenario
- github_publication_review

## Boundary

- do not start fcron
- do not manage OpenRC
- edit the concerned fcron table without duplicates
- scan-once command only
- no GitHub API call
- no GitHub mutation
- no SQL write
- no Qdrant write
- no Scheduler execution
- no LLM execution
- no OpenVINO execution
