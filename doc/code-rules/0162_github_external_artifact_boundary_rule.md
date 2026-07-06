# Code rule — 0162 GitHub external artifact boundary

## Rule

Do not use the development repository as the source of idea artifacts.

The Autodoc/MissiPy development repository is infrastructure/control-plane code.
It contains patch queue work, tests, architecture docs and local smokes. It must
not be treated as the business corpus for SQL/Qdrant ingestion.

## Required source

The idea source must be an explicit external artifact repository or GitHub
Project surface.

For the 0162 smoke, the example external artifact repository is:

```text
newicody/autodoc-ideas
```

A future operator may use another repository, but it must be explicit and must
not equal the Autodoc/MissiPy development repository.

## Required flow

The intended flow is:

```text
external GitHub Project item
-> GitHub Action/Copilot artifact
-> local server import
-> specialist/scheduler processing
-> synthesis
-> publication review packet
-> GitHub response artifact only after review
```

## Forbidden in 0162

- no SQL write
- no Qdrant write
- no GitHub API call
- no external network
- no Scheduler execution
- no LLM execution
- no OpenVINO execution
- no automatic publication
- no ingestion of patch files, tools, tests or Autodoc development repo material

## Required reuse

0162 must reference existing GitHub/external surfaces instead of inventing a
new GitHub runtime:

- `github_project_scenario.py`
- `server_oriented_deliberation_cycle.py`
- `github_publication_review.py`
- `source_candidate_github_projection_payload.py`
- `source_candidate_external_projection_contract.py`
- `source_candidate_read_only_external_probe.py`
- `source_candidate_remote_mutation_gate.py`
- `source_candidate_external_probe_bundle.py`

## Publication

Publication back to GitHub requires a publication review packet and a later
reviewed adapter. There is no automatic publication in this phase.
