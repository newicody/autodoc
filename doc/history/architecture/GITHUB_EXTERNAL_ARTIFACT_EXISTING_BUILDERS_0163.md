# 0163 — GitHub external artifact existing builders

## Decision

0163 refactors the 0162 smoke to reuse existing builders instead of keeping a
parallel JSON-only GitHub model.

The smoke remains local-only and keeps the 0162 source boundary:

```text
Autodoc/MissiPy development repository = infrastructure
external GitHub Project repository = source of idea artifacts
```

## Builders reused

The smoke must reuse existing builders and contracts:

- `GitHubProjectArtifact`
- `build_github_source_candidate`
- `build_github_context_objective`
- `build_github_project_scenario_packet`
- `build_github_project_context_graph`
- `export_context_graph_dot`
- `build_github_publication_review`
- `render_github_publication_review_markdown`
- `build_context_exploration_plan`
- `LLMSolutionCandidate`
- `LLMSpecialistResult`
- `build_server_orientation_from_github_artifact`

## Flow

```text
external GitHub artifact fixture
-> GitHubProjectArtifact
-> build_github_source_candidate
-> build_context_exploration_plan
-> LLMSpecialistResult fixture packet
-> build_github_project_scenario_packet
-> build_github_project_context_graph
-> build_github_publication_review
-> local review markdown/json
```

## Boundary

0163 does not perform runtime side effects:

- no SQL write
- no Qdrant write
- no GitHub API call
- no external network
- no Scheduler execution
- no LLM execution
- no OpenVINO execution
- no automatic publication

## No new GitHub model

0163 must not create a parallel GitHub model, adapter, orchestrator or runtime.
The only new logic allowed is CLI glue around existing contracts.


Boundary phrase: no new GitHub model.
