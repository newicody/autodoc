# Route generation table — 0091-r2

Status: implementation patch.

0091-r2 implements the ControlProxy route generation table proposed during the
operational review:

```text
route_id -> current_generation
```

In this phase, the table is represented as deterministic JSON under
`active/routes/<route_id>/generation_state.json`. A generation record is also
written under `active/routes/<route_id>/generations/gN/status.json`.

The generation counter is incremented only when a new route generation is materialized.
It is not incremented for normal route writes, normal route reads,
notifier wakeups, selector drains, or ordinary Scheduler handshakes.

## Operational path

```text
ready RoutePrepareDecision(create_route_generation/create_next_generation)
-> load generation_state.json
-> verify decision.next_generation == table.next_generation
-> create route@gN/ring.bin
-> write generation gN as candidate
-> increment table.next_generation to N+1
```

This gives the ControlProxy side an explicit g2/g3 allocation state without
resizing a live mmap route.

## No live resize

The active data surface is never resized in place.

```text
routes/route-a@g1/ring.bin  # existing generation
routes/route-a@g2/ring.bin  # new candidate generation
routes/route-a@g3/ring.bin  # later candidate generation
```

The future /dev/shm placement can use the same model. 0091-r2 is Not
/dev/shm-only; the current runtime root is file-backed mmap and can later point
to /dev/shm.

## Boundaries

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No live mmap resize.
- No inter-process lock yet.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- Activation, drain, and closed cleanup remain for 0092.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0091-r2 adds an importable ControlProxy-side materialization
primitive and a deterministic table. It does not add a CLI, daemon, watcher,
network path, backend, Scheduler modification, Qdrant, LLM, or OpenVINO path.
