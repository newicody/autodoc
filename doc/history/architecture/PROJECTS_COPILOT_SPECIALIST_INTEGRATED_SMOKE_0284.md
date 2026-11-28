# Projects/Copilot/portable-specialist integrated smoke — 0284-r7

## Purpose

Close the first integrated local path from correlated artifacts produced in
`newicody/projects` to one portable fake specialist using the real memory
bindings already proven by 0284-r6.

## Composition

```text
GitHubDualArtifactRunMember
  → GitHubDualArtifactRunAssemblyCommand (0281)
  → validated authoritative request and Copilot advisory
  → GitHubCopilotAdvisoryLaboratoryProjection (0281)
  → context reference injected in PortableSpecialistRealMemoryClosureCommand
  → 0284-r6
  → controlled Issue publication plan (0281)
  → ProjectV2 field preview consumed by the copied Projects bundle
```

The project views are not owned or reconciled by Autodoc runtime code. Their
configuration remains under `templates/github/projects-repository/` until it
is copied to `newicody/projects`.

## Authority

```text
request = authority
operator decision = execution/publication gate
Copilot = consultative hint
Scheduler = sole orchestrator
SQL = durable authority
Qdrant = projection and reference-only recall
EventBus = observation only
GitHub/ProjectV2 = review and workflow surfaces
```

## No-write result

The smoke returns an idempotent Issue comment plan and a ProjectV2 field
preview. Separate explicitly authorised adapters execute them later.

```text
github_mutation_performed: false
projectv2_mutation_performed: false
```
