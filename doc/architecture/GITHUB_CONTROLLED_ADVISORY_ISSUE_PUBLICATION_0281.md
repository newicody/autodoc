# GitHub controlled advisory Issue publication — 0281-r6

## Purpose

Publish the operator-approved Copilot advisory and laboratory preview as one
idempotent GitHub Issue comment.

The publication is performed by the local Autodoc server/operator, not by the
GitHub Actions producer:

```text
r5 local publication preview
-> local read of existing Issue comments
-> pure create/replay/collision plan
-> explicit operator review of plan_digest
-> local execute command
-> one GitHub Issue comment
```

## Authority and safety

The comment states that Copilot is consultative and non-authoritative. The
request and operator decision remain authority.

Execution requires all of:

```text
operator_decision = approve
policy_decision_id starts with policy:
--execute
--confirm-plan-digest exactly matches the previewed plan
```

Default mode never mutates GitHub.

## Idempotency and collision guard

A deterministic invisible marker is derived from repository, Issue,
SourceCandidate and advisory artifact:

```text
<!-- autodoc:copilot-advisory:<24-hex-digest> -->
```

Behavior:

```text
marker absent                         -> create
one identical marked comment          -> replay, no mutation
one different marked comment          -> collision, block
multiple matching marked comments     -> collision, block
```

No marked comment is updated or deleted automatically.

## Adapter boundary

The pure contract is in `src/context`. The local adapter in `tools` uses the
already-installed GitHub CLI to list comments and, only after exact digest
confirmation, create a comment.

The adapter does not use Scheduler, SQL, Qdrant, EventBus, OpenVINO or a
laboratory runtime.

## Repository impact

```text
newicody/autodoc: modification required
newicody/projects: no Git-tracked modification required
projects_repository_change_required: false
workflow permissions remain unchanged
```

The workflow remains `issues: read`. This is intentional: the workflow that
creates the advisory cannot self-authorize its publication. The local `gh`
identity must independently have Issue write permission when `--execute` is
used.

A remote Issue comment is data written through the explicit local adapter; it
is not a commit or workflow change in `newicody/projects`.
