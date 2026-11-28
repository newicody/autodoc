# Cell Snapshot SSE Stream Contract v1

```text
schema: missipy.cell_snapshot_sse.v1
event: cell_snapshot
payload snapshot schema: missipy.cell.v1
```

This contract defines the read-only Server-Sent Events text format for the
future Phase 10 local mobile/browser view.

It is not a server yet.

It is no command channel.

## Purpose

```text
same missipy.cell.v1 journal
→ replay/tail reader
→ SSE text event
→ local server later
→ browser window later
```

The browser is a window. The local machine and the journal remain the source of
truth.

## Event shape

```text
id: <sequence>
event: cell_snapshot
data: {"schema":"missipy.cell_snapshot_sse.v1","snapshot":{...missipy.cell.v1...}}
```

Each SSE event carries one cell snapshot.

## Boundary rule

The contract may format text. It must not open sockets, expose a server
endpoint, import a browser framework, import VisPy, or dispatch actions.

Phase 10 may later add a local server that streams this exact contract.

## Command rule

The mobile/browser view is read-only.

Any future action must use:

```text
typed command → Scheduler
```

It must not travel through SSE, the journal, replay state, or the browser view.
