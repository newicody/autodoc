# Changelog — 0285-r6

## Added

- immutable Scheduler revision-selection policy, command and result;
- pure selector requiring the latest durable operator-approved r5 history entry;
- Dispatcher-compatible async handler;
- event builder and existing-Dispatcher registration helper;
- `SPECIALIST_REVISION_SELECTION` and reserved result event types appended to
  `EventType` without renumbering earlier members;
- capability, contract, laboratory and execution-boundary validation;
- context tests, architecture rules, report, documentation, graph and manifest.

## Unchanged

- one central Scheduler;
- SQL authority and Qdrant projection/recall boundary;
- EventBus observation-only role;
- laboratory execution path;
- GitHub Projects workflows and cumulative installation guide.

## Next

`0285-r7-specialist-capability-growth-observation-projection`
