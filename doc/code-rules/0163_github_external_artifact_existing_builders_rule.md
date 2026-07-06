# Code rule — 0163 GitHub external artifact existing builders

## Rule

Use the existing builders before adding any new GitHub runtime or schema.

Do not create a parallel GitHub model when `github_project_scenario.py`,
`github_publication_review.py`, `context_graph_export.py`,
`context_variation_core.py`, `llm_specialist_adapter.py`, and
`server_oriented_deliberation_cycle.py` already provide the required contracts.

## Required builders

The GitHub external artifact smoke must use:

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

## Forbidden

- No new adapter
- No new orchestrator
- No new GitHub model dataclasses
- No SQL write
- No Qdrant write
- No GitHub API call
- No external network
- No Scheduler execution
- No LLM execution
- No OpenVINO execution
- No automatic publication

## Boundary

0163 is a local-only existing-builder smoke. It proves that the GitHub external
artifact path can be expressed through existing contracts before any real
GitHub read-only fetch/import work begins.
