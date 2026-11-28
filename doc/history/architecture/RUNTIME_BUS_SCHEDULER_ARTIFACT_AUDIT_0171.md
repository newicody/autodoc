# 0171 — Runtime bus/scheduler artifact audit

## Decision

0171 is an audit and guard patch. It intentionally does not add a new fetcher,
converter, scheduler, bus, watcher, daemon, or VisPy writer.

The GitHub artifact pipeline must reuse the existing runtime observation and
scheduler surfaces:

- `src/runtime/bus_visualization_adapter.py`
- `src/runtime/scheduler_route_adapter.py`
- `src/runtime/scheduler_route_handler_minimal.py`
- `src/runtime/scheduler_route_handshake.py`
- `src/runtime/shm_runtime_schema.py`

## Locked boundary

VisPy/browser views read existing `event.bus/context.bus` facts through the
existing bus visualization adapter.

GitHub artifact fetch, dataset sync, attachment handling, and conversion
planning must not write directly to VisPy and must not create a parallel bus.

The existing `event.bus/context.bus` path remains the canonical observation
surface. Dataset-local files such as observation journals may exist for audit
or staging, but they are not the canonical VisPy integration path.

Scheduler/policy/zone remain the authority. EventBus is observation-only.
Events and bus facts are facts, not commands.

## Audit of recent phases

### 0165

0165 is compatible with this boundary. It defines configuration and fcron table
text for polling, but does not implement a runtime bus, scheduler loop, or
VisPy writer.

### 0166

0166 is compatible. It defines GitHub Action ticket artifacts and a Copilot
preliminary opinion artifact. It does not integrate with runtime bus or VisPy.

### 0167

0167 is useful as a server dataset sync contract. However, any `vispy_events`
or similarly named dataset directory must be treated only as a local observation
journal or staging file. The canonical VisPy/browser path is still the existing
`event.bus/context.bus` adapter.

### 0168

0168 may fetch GitHub Actions artifacts read-only into server staging/dataset
surfaces. It must not notify VisPy directly and must not become a scheduler.

### 0170

0170 is compatible. It creates a metadata-only attachment manifest with GitHub
issue attachment references. It does not store user attachments in the Autodoc
repository and does not publish runtime observations.

### Superseded 0171 attachment fetch attempt

The earlier generated `0171-github_attachment_reference_fetch` patch is
superseded. It was extracted only as development history and must not be used as
the next functional step until the artifact pipeline is reconnected to the
existing bus/scheduler surfaces.

## Required next integration

The next functional patch should bridge GitHub artifact/dataset outcomes into
existing bus-compatible observation facts, or into scheduler-addressable command
data, without creating a parallel observation path.

A valid implementation should prefer existing surfaces before adding any new
runtime module. If a new adapter is needed, it must document why
`bus_visualization_adapter`, `scheduler_route_adapter`,
`scheduler_route_handler_minimal`, `scheduler_route_handshake`, or
`shm_runtime_schema` cannot be extended directly.

## Non-goals

- No GitHub API call in this audit patch.
- No network.
- No remote mutation.
- No conversion execution.
- No inference.
- No SQL write.
- No qdrant write.
- No new EventBus.
- No parallel bus.
- No direct VisPy writer.
- No Scheduler.run() modification.
