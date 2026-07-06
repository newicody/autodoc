# Code rule — 0156 surface status inventory

0156 is a classification and repository hygiene phase.

## Required

Before adding any new runtime, handler, adapter, worker, runner, orchestrator,
store, vector backend, Scheduler loop, or GitHub integration, the patch must
inspect existing surfaces and state one of:

```text
reuse
extend
wrap
supersede
deprecate
blocked
```

## Allowed in 0156

- Add documentation.
- Add a status vocabulary.
- Add one phase DOT under `doc/docs/architecture/runtime/`.
- Remove generated SVG artifacts from `doc/docs/architecture/` when existing
  rules require `.dot` source-only architecture files.

## Forbidden in 0156

- Creating a new SQL worker.
- Creating a new Scheduler runner.
- Creating a new local orchestrator.
- Creating a new RouteProxy business authority.
- Creating a new Qdrant authority.
- Creating a new OpenVINO reasoning backend.
- Creating a new GitHub API/token/polling path.
- Deleting Python runtime code.
- Marking code as abandoned without proof.

## Status vocabulary

Allowed statuses:

```text
current
validated
partial
planned
historical
superseded
deprecated
blocked
```

`abandoned` is not allowed in 0156.

## Boundary reminders

- Scheduler remains the orchestrator.
- RouteProxy/ControlProxy remains fast data-plane / frame control.
- SQL remains durable authority.
- Qdrant remains projection and recall only.
- E5 produces embeddings.
- OpenVINO executes E5 locally.
- EventBus observes; it does not command.
- GitHub is a future artifact/project exchange surface, not the internal bus.
