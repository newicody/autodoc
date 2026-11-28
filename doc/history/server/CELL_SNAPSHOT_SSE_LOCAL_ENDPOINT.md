# Cell Snapshot SSE Local Endpoint

This endpoint serves the same missipy.cell.v1 journal as read-only SSE.

It is local-only.

```text
host: 127.0.0.1
path: /cells.sse
health: /health
```

## Purpose

```text
same missipy.cell.v1 journal
→ replay/tail reader
→ SSE contract
→ local read-only endpoint
→ browser window
```

The endpoint is a window into the journal. It is not a source of truth.

## Read-only rule

No POST.
No PUT.
No DELETE.
No command channel.

The endpoint returns `405 Method Not Allowed` for write-like HTTP methods.

## Local-only rule

The default host is `127.0.0.1`.

The tool rejects any other host for this phase.

## Usage

```bash
PYTHONPATH=src:. python tools/cell_snapshot_sse_server.py \
  --journal /tmp/missipy_cells.jsonl \
  --port 8765
```

Follow a growing journal:

```bash
PYTHONPATH=src:. python tools/cell_snapshot_sse_server.py \
  --journal /tmp/missipy_cells.jsonl \
  --port 8765 \
  --tail
```

Then open:

```text
http://127.0.0.1:8765/cells.sse
```

## Boundary

The server tool must not import visualization code, command code, model code, or
external API clients.
