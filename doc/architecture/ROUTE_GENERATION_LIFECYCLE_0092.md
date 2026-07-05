# Route generation lifecycle — 0092

Status: implementation patch.

0092 adds importable lifecycle helpers for the route generation table introduced
in 0091-r2. The operational state path is explicit:

```text
candidate -> active -> draining -> closed -> cleanup closed generation
```

The cleanup entry point is `cleanup_closed_route_generation()`. It removes only
the runtime route directory belonging to a closed generation and writes a small
cleanup status record under ControlFS.

## Operational path

```text
materialized route@gN candidate
-> activate_route_generation()
-> mark_route_generation_draining()
-> mark_route_generation_closed()
-> cleanup_closed_route_generation()
```

The cleanup function verifies that the persisted runtime route directory matches
`runtime_root/routes/<route_handle>` before deleting anything. Cleanup is limited
to closed generations only. Candidate, active, and draining generations are
rejected.

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
- No Qdrant, LLM, OpenVINO, network, or GitHub API path.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0092 adds a small importable lifecycle/cleanup primitive for
already materialized route generations. It keeps effects at the route runtime
boundary, preserves Scheduler/policy/zone authority, and does not add a CLI,
daemon, watcher, service, backend, Scheduler modification, Qdrant, LLM, or
OpenVINO path.
