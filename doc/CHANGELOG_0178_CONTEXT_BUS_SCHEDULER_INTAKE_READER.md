# Changelog — 0178 Context bus scheduler intake reader

## Added

- Reader from existing `context.bus.jsonl` to GitHub artifact scheduler intake
  plans.
- Strict topic and payload schema filtering for GitHub artifact dataset context
  facts.
- CLI that reads `--context-bus` rather than arbitrary scheduler intake JSON.
- Tests/rules locking that Scheduler, EventBus, route handler, GitHub API,
  network, conversion, inference, SQL, Qdrant, and VisPy remain untouched.

## Not changed

- No Scheduler modification.
- No EventBus instantiation.
- No route execution.
- No GitHub API.
