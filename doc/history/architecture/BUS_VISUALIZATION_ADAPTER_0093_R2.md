# Existing bus visualization adapter — 0093-r2

Status: implementation patch.

0093-r2 replaces the rejected 0093 direction. The adapter reads existing
event.bus/context.bus objects. It does not instantiate EventBus, does not create
a new bus, and does not build a parallel observation path. It only attaches a
read tap to an already-created event bus and reads the already-produced context
snapshot source.

## Operational path

```text
existing EventBus + existing context source
-> event_bus.subscribe() read tap
-> drain_existing_event_bus_reader()
-> read_existing_bus_visualization_snapshot()
-> ExistingBusVisualizationSnapshot.to_mapping()
-> VisPy/browser renderer later
```

The subscription is a read handle on the existing EventBus. It is not a new bus
and it is not an execution authority. Context is read from an existing
GlobalContextSnapshot, mapping snapshot, or object exposing last_snapshot such
as the current ContextEngine. The adapter is a one-shot read/projection layer.

## Boundaries

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No kernel loop modification.
- EventBus is observation only.
- Events/bus facts are facts, not commands.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- The adapter reads existing event.bus/context.bus objects.
- The adapter does not instantiate EventBus.
- The adapter does not create a parallel bus.
- No Qdrant.
- No LLM.
- No OpenVINO.
- No network, GitHub API, VisPy dependency, or browser launch.
- stdlib only.

## Why attach instead of create

The system already defines EventBus as the observation channel. 0093-r2 must not
invent a new bus for visualization. A visualization surface should receive the
same facts as other observers by subscribing to the existing bus and by reading
the existing context snapshot source.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0093-r2 adds a small importable projection adapter for
existing observable bus facts. It does not add a CLI, daemon, watcher, service,
backend, Scheduler modification, Qdrant, LLM, OpenVINO, network path, VisPy
dependency, browser runtime, or parallel bus. EventBus remains observation only
and Scheduler/policy/zone remain the authority.
live_path_status: green
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
