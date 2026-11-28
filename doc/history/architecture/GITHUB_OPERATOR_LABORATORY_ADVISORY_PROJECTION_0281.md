# GitHub operator/laboratory advisory projection — 0281-r5

## Purpose

Project the complete, validated Copilot advisory into the existing fake
laboratory path without changing authority or orchestration.

```text
0275 intake
-> explicit promote/merge operator decision
-> hint-only advisory context projection
-> existing 0275 laboratory smoke
-> existing Scheduler
-> existing 0274 fake laboratory closed loop
-> local publication preview
```

## Projection

The advisory is retained as a structured mapping containing its summary,
suggested route, assumptions, questions, risks, confidence, producer and
correlation identifiers.

A deterministic typed reference is derived:

```text
ctx:github-advisory:<digest>
```

The reference is added to `ServerOrientation.context_refs`. The orientation
also receives two explicit directives:

- use the advisory only as a consultative hypothesis;
- never interpret it as authority, validation, policy approval or publication
  authorization.

The full advisory remains available in the result mapping and raw artifact.
It is not copied into the authoritative request or SourceCandidate body.

## Existing path reuse

This phase reuses:

- `run_github_dual_artifact_source_candidate_intake` from 0275;
- `GitHubDualArtifactLaboratorySmokeCommand` from 0275;
- `run_github_dual_artifact_laboratory_smoke` from 0275;
- the existing Scheduler and fake laboratory closed loop from 0274.

No Scheduler, queue, EventBus, manager, registry or laboratory orchestrator is
created.

## Operator boundary

Only `promote` or `merge` decisions may enter this path. The immutable
`policy_decision_id` must start with `policy:`.

The resulting publication content is still only a local preview. Remote
mutation remains forbidden until 0281-r6 reuses the 0276 controlled publication
boundary and collision guard.

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: no modification required
projects_repository_change_required: false
```

The GitHub workflow already emits the complete advisory. This patch is entirely
inside the local Autodoc context/laboratory composition.
