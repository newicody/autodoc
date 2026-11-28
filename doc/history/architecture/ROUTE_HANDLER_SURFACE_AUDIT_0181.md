# 0181 — Route handler surface audit

## Decision

0181 audits existing route handler surfaces before execution.

It does not execute the route handler.
It does not import handler modules.
It reads files as text and AST only.

0181 must run before any patch attempts a real handler handoff.

## Why this exists

0179 creates `scheduler.route_requests.jsonl`.
0180 audits that queue as structurally ready.

Before a future patch calls any existing route handler surface, we need an exact
read-only inventory of the local files and symbols that already exist. This
respects the main code rule: audit existing code and reuse/extend it before
creating any new runtime handler.

## Audited surfaces

The audit tracks these existing surfaces:

```text
src/runtime/scheduler_route_adapter.py
src/runtime/scheduler_route_handler_minimal.py
src/runtime/scheduler_route_handshake.py
src/runtime/controlproxy_scheduler_handler.py
```

The report includes:

- file presence,
- SHA256 of the local file content,
- AST parse status,
- expected symbols found/missing,
- imports detected by AST.

## Boundary

0181:

- reads source files,
- parses AST,
- writes a report to stdout through the CLI.

0181 does not:

- import runtime handler modules,
- call handle_scheduler_route_request,
- instantiate Scheduler,
- modify Scheduler.run,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
The audit report does not grant execution.
