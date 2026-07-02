# Cell Lens Architecture

The cell lens is an observation-only visualization architecture for MissiPy.

It shows a population of cells representing task/component activity without
becoming part of the command path. The cell lens must not command the system.

## Strong boundary

```text
Observation:
  EventBus
  recorder
  replay
  cell snapshot journal
  VisPy / browser / analysis scripts

Command:
  typed command
  Scheduler
  kernel command handling
```

The observation path may lose, aggregate, or delay data under load. The command
path must remain explicit and typed.

## Lens, not lever

The cell lens may observe:

```text
task lifecycle
component origin
age
cost
score
health estimate
```

The cell lens must not:

```text
schedule work
cancel work
mutate component state
publish commands on the EventBus
be required for deterministic execution
```

Any future operator action from a visualization must leave the visualization as
a typed command submitted to the Scheduler. The action must not travel through
the EventBus.

## Shared snapshot contract

All renderers and analysis tools consume the same versioned contract:

```text
missipy.cell.v1
```

Consumers include:

```text
VisPy desktop viewer
future local mobile browser view
offline analysis scripts
replay/debug tools
```

If new data is needed, a new version is introduced. Existing fields in
`missipy.cell.v1` are not silently repurposed.

## Journal as boundary

The journal is the stable bridge between the running system and visualization.

```text
EventBus observation events
→ recorder boundary
→ JSONL cell snapshot journal
→ replay/tail reader
→ visualization or analysis
```

Live mode is only replay that has caught up to the file end.

## Health rule

Health is not raw speed.

A cell is healthy when its observed lifecycle is close to the expected lifecycle
for its source class.

```text
LLM response slow but expected: healthy
short task unexpectedly slow: unhealthy
long ingestion batch within expected window: healthy
```

The first implementation may use simple expected lifetime tables by source
class. Optimization loops are not part of this phase.

## Dependency rule

VisPy is a desktop visualization boundary dependency. It must not be imported by
kernel, contracts, Scheduler, EventBus, recorder core, or replay core modules.

Core code may define contracts and journal readers. UI code may depend on core
contracts. Core code must not depend on UI code.
