# 0164 — GitHub read-only artifact fetch smoke

## Decision

0164 prepares the first read-only GitHub artifact fetch/import boundary without
creating a new GitHub adapter.

It is a local dry run that must reuse existing builders:

- `FakeSourceCandidateReadOnlyExternalProbeAdapter`
- `build_source_candidate_read_only_external_probe_request_from_file`
- `build_source_candidate_external_probe_bundle`
- `build_source_candidate_external_projection_contract`
- `build_source_candidate_github_projection_payload`
- `run_source_candidate_remote_mutation_gate`

This phase is read-only artifact fetch preparation, not a real network fetch.

## Flow

```text
operator external review report
-> read-only probe request
-> existing fake read-only probe adapter
-> read-only probe result
-> SourceCandidateExternalProbeBundle
-> SourceCandidateExternalProjectionContract
-> SourceCandidateGithubProjectionPayload
-> remote mutation gate remains closed
```

## Boundary

- reuse existing builders
- no new GitHub model
- no new GitHub adapter
- no new orchestrator
- no GitHub API call
- no external network
- no SQL write
- no Qdrant write
- no Scheduler execution
- no LLM execution
- no OpenVINO execution
- no automatic publication
- remote mutation gate remains closed

## Repository boundary

The external artifact repository must be explicit and must not equal the
Autodoc/MissiPy development repository.

Example:

```text
development repository: newicody/autodoc
external repository: newicody/autodoc-ideas
```

## Smoke command

```text
python tools/run_github_read_only_artifact_fetch_smoke.py . --execute --format json
```

## Expected result

```text
status: ok
read_only: true
probe_allowed: true
external_call_performed: false
github_payload_dry_run: true
github_payload_remote_mutation: false
mutation_allowed: false
```

The smoke may create local JSON/Markdown artifacts under `.var/smoke`, but it
does not write SQL/Qdrant and does not contact GitHub.
