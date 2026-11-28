# Changelog — 0287-r7-r8-r6

## Added

- versioned authorization, execution-target, task-state, mutation, receipt,
  laboratory-notification, command, item and report contracts;
- `SchedulerContextImpactExecutionHandler` on the existing Dispatcher event
  boundary;
- deterministic in-memory Scheduler task-mutation reference port;
- route-adapter invocation only for explicit transport transitions;
- Event contract values for execution, execution result and laboratory context
  update;
- targeted positive, replay, drift, collision and negative-path tests.

## Changed

- current roadmap records the executable r8-r6 closure and r9 as the next unit.

## Unchanged

- Scheduler implementation and queue ownership;
- EventBus implementation;
- ControlProxy implementation and route-generation lifecycle;
- SQL context-revision schema and stored data;
- Qdrant profiles, collections and points;
- OpenVINO adapters and models;
- GitHub/ProjectV2 deployment bundle and installation guide.
