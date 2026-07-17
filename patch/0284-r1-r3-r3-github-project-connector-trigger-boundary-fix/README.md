# 0284-r1-r3-r3 — GitHub connector trigger boundary fix

Apply this patch on the dirty worktree left by the successful application of
`0284-r1-r3-r1` and `0284-r1-r3-r2`, after the full-suite failure on
`artifact_source.trigger_source`.

The patch does not revert the configuration split. It restores the existing
read-only artifact-ingestion contract (`github_action_on_ticket_event`) while
keeping outbound `workflow_dispatch` exclusively in
`config/github_projects_workflow_dispatch.example.ini`.

Suggested commit:

```text
split-github-project-connector-configs
```
