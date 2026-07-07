# Changelog — 0176 GitHub artifact dataset bus observation bridge

## Added

- Pure bridge from GitHub artifact/server dataset outcome mappings to existing
  `EventBusMessage` and `ContextBusMessage` runtime schema objects.
- Optional explicit JSONL append to `event.bus.jsonl` and `context.bus.jsonl`.
- CLI for projecting one local JSON observation file to existing bus JSONL.
- Tests and rules locking that no parallel bus, direct VisPy writer, Scheduler
  bypass, GitHub API call, network, conversion, inference, SQL, or Qdrant write
  is introduced.

## Not changed

- No Scheduler modification.
- No EventBus instantiation.
- No VisPy renderer.
- No GitHub API.
- No network.
