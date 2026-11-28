# GitHub pinned and cached Copilot CLI runtime — 0281-r4

## Decision

The workflow pins GitHub Copilot CLI to `1.0.70` and caches the complete
workflow-local npm prefix:

```text
${{ github.workspace }}/.cache/copilot-cli
```

The exact key is scoped by cache schema, runner OS, runner architecture and
Copilot CLI version. No broad restore key is used.

## Execution

```text
cache restore
-> exact hit: skip npm installation
-> miss: npm install @github/copilot@1.0.70 into local prefix
-> verify package version and executable
-> call it through AUTODOC_COPILOT_COMMAND
```

`COPILOT_AUTO_UPDATE=false` preserves the pinned runtime.

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: modification required
projects_repository_change_required: true
```

`newicody/projects` must deploy the workflow and allow `actions/cache@v4` in
its selected-actions policy.

## Boundaries

```text
Scheduler modification: none
SQL/Qdrant modification: none
GitHub mutation: none
Copilot remains consultative and non-authoritative
```
