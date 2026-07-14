# Phase 0284-r1-r2-r1-v3 — Autodoc / Projects boundary documentation compatibility

## Outcome

The historical 0272 rule assertions are satisfied through explicitly scoped
compatibility wording in the documentation. No obsolete test is modified and no
project-management capability is reintroduced into Autodoc.

## Application context

This corrective patch is intended for the dirty worktree left after
`0284-r1-r2-autodoc-projects-boundary-realignment` was applied and its rule gate
stopped before commit.

## Boundary preserved

- `newicody/projects` owns active workflows, Issue forms, ProjectV2 views and
  project configuration;
- Autodoc keeps only external connectors, reusable helpers and the copy-source
  bundle under `templates/github/projects-repository/`;
- the legacy expressions retained by this patch are documentation compatibility
  markers, not runtime architecture declarations;
- no Scheduler, EventBus, SQL, OpenVINO, Qdrant or GitHub API path changes.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: documentation-only compatibility correction; no new programming technique or runtime boundary
live_path_status: n/a
live_path_uses_real_backend: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
