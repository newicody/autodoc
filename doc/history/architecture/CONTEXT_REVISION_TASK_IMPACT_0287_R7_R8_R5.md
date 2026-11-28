# Context revision task-impact policy — 0287-r7-r8-r5

## Purpose

Bind each specialist task to one accepted SQL semantic revision and compute an
effect-free Scheduler decision proposal when a direct accepted child revision
changes the knowledge used by that task.

## Flow

```text
SQL semantic revision rN
→ accepted child revision rN+1
→ reference-only change set
→ task/revision binding
→ dependency and significance assessment
→ Scheduler decision proposal
→ later Scheduler/EventBus/ControlProxy execution adapter
```

## Policies

- `snapshot`: continue against the original revision;
- `checkpoint_rebase`: wait for a declared safe checkpoint, then rebase;
- `restart_on_material_change`: restart from the accepted target revision;
- `fork_on_material_change`: preserve the current execution and compare a new branch;
- `notify_only`: notify without changing execution;
- `ignore_noncritical`: ignore minor/material changes and notify on critical change.

Completed results are never rewritten. They remain reproducible against their
bound revision and may be marked stale against a newer revision.

## Boundaries

- SQL semantic revision is authoritative.
- Scheduler alone authorizes and executes an action.
- EventBus observes later execution; it does not decide.
- ControlProxy remains transport-only and does not own knowledge or policy.
- No task, route, event, SQL row or Qdrant point is changed by this phase.
