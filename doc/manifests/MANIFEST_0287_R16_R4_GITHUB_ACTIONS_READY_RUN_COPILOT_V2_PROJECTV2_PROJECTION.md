# Manifest — 0287 r16-r4

## Added runtime surfaces

- `src/context/github_actions_ready_run_copilot_v2_projection_0287.py`
- `tools/run_github_actions_ready_run_copilot_v2_projection_0287.py`

## Reused surfaces

- `templates/github/projects-repository/scripts/build_copilot_advisory_v2_publication_preview.py`
- `templates/github/projects-repository/scripts/project_copilot_advisory_fields.py`
- `templates/github/projects-repository/scripts/project_copilot_advisory_v2_fields.py`

## Tests

- `tests/test_github_actions_ready_run_copilot_v2_projection_0287.py`
- `tests/rules/test_github_actions_ready_run_copilot_v2_projection_0287_r16_r4_rule.py`

## Architecture boundaries

Local raw dataset is the only artifact input. GitHub is contacted only by the
existing ProjectV2 GraphQL adapter for inventory, explicit mutation and
readback. SQL, Qdrant, laboratory and Scheduler remain untouched.
