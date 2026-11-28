# 0098 — ControlProxy dispatch filtering envelope

Status: operational architecture and importable envelope.

0098 adjusts the wording introduced around ControlProxy, ControlFS, Scheduler
policy, and zones. The route proxy path uses a security-shaped envelope, but its
operational purpose in this part of the Scheduler is dispatch filtering.

```text
policy/zone dispatch filtering
not a security objective
```

## Correct interpretation

The Scheduler side still owns the policy and zone decision:

```text
Scheduler/policy/zone remain the authority.
```

ControlProxy does not decide security policy. It reads an already-decided
Scheduler envelope and uses it to filter route dispatch, select the coherent
route-control path, and prevent malformed work from entering ControlFS.

So the meaning is:

```text
Scheduler/policy/zone decide authority.
ControlProxy/ControlFS apply policy/zone dispatch filtering.
Dispatcher remains required between Scheduler.run() and ControlProxy.
```

This is not a contradiction with the security-shaped vocabulary. The envelope
contains `authorized=True`, `policy_decision_id`, `zone`, and `route_id`, but
ControlProxy treats those fields as dispatch-filtering metadata. It may reject a
malformed or non-authorized envelope, but this remains a boundary filter, not a new security decision.

## Importable capability

0098 adds `RouteDispatchFilterEnvelope` and `RouteDispatchFilterDecision`.

```text
payload from Scheduler-facing request
-> evaluate_route_dispatch_filter(payload)
-> accepted/rejected dispatch-filter decision
-> RouteDispatchFilterEnvelope(route_id, zone, policy_decision_id, authorized)
```

The envelope is intentionally small:

```text
route_id
zone
policy_decision_id
authorized
source
metadata
```

It has no I/O, no Scheduler dependency, no EventBus dependency, no ControlFS
write, and no backend dependency. It is a typed filter envelope that can later be
called by the ControlProxy handler before materialization.

## Graph integration rule

The graph remains integrated in the root Runtime ControlFS / SHM / Cluster
Fabric graph. The ControlProxy/ControlFS cluster should show dispatch filtering
inside the bounded subsystem, not as an isolated security box.

```text
Root graph, not an isolated phase graph.
```

The intended structure is:

```text
SecurityFS / policy / zones
-> Scheduler / PolicyEngine
-> PriorityQueue / Scheduler.run()
-> Dispatcher
-> ControlProxy route handler
-> RouteDispatchFilterEnvelope
-> ControlProxy/ControlFS route-control block
-> locked generation materializer
-> runtime placement
-> g2/g3 route generations
```

## Scheduler.run() status

The lock remains in force:

```text
No Scheduler.run() modification.
```

There is no need to loosen that constraint for 0098. The current Dispatcher -> Handler path is still sufficient. The loop can be reopened later only for an
explicit kernel-loop design, not to shortcut ControlProxy integration.

## Relation to previous phases

0098 clarifies the general architecture after:

```text
0088 concrete Scheduler handler boundary
0089 write -> notify -> selector/drain
0090 RouteMessage journal
0091-r2 route_id -> current_generation table
0092 candidate -> active -> draining -> closed cleanup
0093-r2 existing event.bus/context.bus adapter
0094 route generation file lock
0095 locked materializer
0096 explicit file|/dev/shm runtime placement
0097 integrated root graph and ControlProxy/ControlFS boundary
```

Nothing in 0098 changes event.bus/context.bus. They remain existing observation
surfaces, not commands and not newly created buses.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: terminology and route dispatch-filter envelope aligned with existing Scheduler/Policy/Dispatcher/Handler rule; no new kernel programming technique is introduced.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

## Boundaries kept

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher, or Component tick contract modification.
- ControlProxy does not decide security policy.
- Scheduler/policy/zone remain the authority.
- The security-shaped envelope is used for policy/zone dispatch filtering.
- EventBus/context bus are existing observation surfaces, not commands.
- No live mmap resize; g2/g3 generations remain the update path.
- Not /dev/shm-only.
- No NetworkBridge or HardwareBridge implementation.
- No Qdrant, LLM, or OpenVINO path.
