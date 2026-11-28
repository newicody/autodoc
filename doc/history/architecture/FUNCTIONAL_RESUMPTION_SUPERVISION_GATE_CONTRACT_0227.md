# Functional resumption supervision gate contract — 0227

## Decision

Functional implementation may resume only after the passive-supervision contracts are treated as the canonical boundary.

The target runtime path remains:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
  -> optional snapshot / optional audit / future VisPy view
```

This patch does not implement that path. It defines the gate that any next functional patch must pass before code is added.

## Why this gate exists

Several candidate directions were rejected before they became permanent architecture:

```text
status JSON first
mandatory events.jsonl bridge
parallel EventBus
new scheduler wrapper
supervisor-owned runtime control
VisPy in the critical path
```

The gate prevents those rejected directions from returning under another name.

## Mandatory pre-implementation audit

Before the next functional patch modifies runtime code, it must inspect the existing repository surfaces and identify reuse targets.

The audit must cover at least:

```text
existing EventBus implementation or event dispatch surface
existing Scheduler event/emission surface
existing passive supervisor / cellular snapshot module from 0220
existing route/control proxy status or event surfaces
existing SHM status/ring/event surfaces
existing policy gate/decision event surfaces
existing GitHub artifact/source-candidate/data-flow contract files
existing SQL/Qdrant recall/projection contract files
```

A new runtime module is allowed only when the audit proves that no existing surface can be safely extended. The reason must be written in the patch documentation.

## Mandatory reuse rule

The next functional patch must prefer extension over invention.

Preferred order:

```text
1. extend existing passive-supervisor module
2. add a small sink class/function inside the existing supervision surface
3. add tests around direct EventBus event acceptance
4. add optional snapshot/audit helpers only if they remain outputs
5. add a new module only after documenting why existing files cannot host it
```

Forbidden default approach:

```text
create new bridge subsystem
create new bus facade
create new scheduler adapter that wraps Scheduler.run()
create file-first replay path as live runtime
create proxy/SHM/policy controller inside supervision
```

## Required functional shape

The next functional patch should target the smallest useful shape:

```text
PassiveSupervisorSink.accept(event)
PassiveSupervisorSink.snapshot()
optional PassiveSupervisorSink.write_snapshot(path)
optional audit writer behind an explicit flag/configuration
```

The sink must accept canonical EventBus events directly. If field normalization is needed, it must be a thin boundary normalization, not a second event grammar.

## Scheduler boundary

The Scheduler remains the upstream orchestration authority.

Allowed:

```text
Scheduler emits an EventBus event
Scheduler exposes an already-produced event to the EventBus
PassiveSupervisorSink observes the resulting event
```

Forbidden:

```text
PassiveSupervisorSink calls Scheduler.run()
PassiveSupervisorSink wraps Scheduler.run()
PassiveSupervisorSink dispatches Scheduler handlers
PassiveSupervisorSink changes Scheduler policy, priority, or order
```

## Proxy / SHM / policy boundary

The runtime surfaces may emit observable events:

```text
RouteProxy route changed
ControlProxy lease or priority changed
SHM ring state observed by owning component
Policy decision allowed / blocked / deferred
```

The supervisor may update cellular state from those events.

It must not:

```text
change a route
claim or release a lease
write to SHM
read raw /dev/shm as a required live path
make or override a policy decision
```

## Data-flow boundary

GitHub, SourceCandidate, SQL, Qdrant, rehydration, and pushback may all produce events that are visible in the same cellular state.

The supervisor observes refs such as:

```text
artifact_ref
source_candidate_ref
sql_ref
qdrant_ref
handoff_ref
pushback_ref
```

It must not perform:

```text
GitHub API mutation
SourceCandidate promotion/rejection
SQL read/write
Qdrant query/write
rehydration execution
pushback publication
```

## Cellular topology requirement

Functional code must preserve the topology concept from 0225.

Cells may be grouped by localization, surface, route, context, owner, or runtime zone. A cell may appear to move when data, a lease, an artifact, a context, or a reference is transmitted elsewhere.

That movement is an observed projection only. It does not transfer authority to the supervisor.

## Snapshot / audit / replay requirement

The live path must stay:

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

Allowed optional outputs:

```text
CellularState -> snapshot.json
PassiveSupervisorSink -> events.jsonl audit
```

Allowed test harness:

```text
events.jsonl fixture -> replay harness -> PassiveSupervisorSink
```

Forbidden live path:

```text
EventBus -> events.jsonl -> supervisor
status.json -> supervisor as primary source
snapshot.json -> live runtime state owner
```

## Acceptance criteria for the next functional patch

The next runtime patch must prove:

```text
no Scheduler.run usage
no new EventBus unless audit-approved
no mandatory events.jsonl/status.json path
no proxy/SHM/policy control
no SQL/Qdrant/GitHub mutation
canonical EventBus event accepted directly
CellularState updated in memory
snapshot available on demand
optional audit remains optional
rule tests updated
changelog and manifest updated
```

## Stop condition

If implementation requires a large adapter or duplicate event grammar, stop and update the EventBus event contract first.

If implementation requires a new module, stop and document the audit result explaining why existing supervision/EventBus surfaces cannot be extended.

## Principle

The functional resumption must make the existing system visible. It must not create a second system.
