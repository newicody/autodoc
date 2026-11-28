# Cell Snapshot Browser Canvas View

This tool serves a local read-only browser window for the Cell Lens.

```text
host: 127.0.0.1
view: /view.html
stream: /cells.sse
health: /health
```

## Purpose

```text
same missipy.cell.v1 journal
→ SSE stream
→ browser EventSource
→ Canvas drawing
```

The browser view is a window over the journal. It is not a source of truth.

## Read-only rule

No command channel.

The page does not use POST, PUT, DELETE, fetch, forms, or remote APIs. It only
opens an EventSource to `/cells.sse` and draws the latest snapshot per cell.

## Local-only rule

The tool binds only to `127.0.0.1` in this phase.

## Usage

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_view_server.py \
  --journal /tmp/missipy_cells.jsonl \
  --port 8766
```

Then open:

```text
http://127.0.0.1:8766/view.html
```

Follow a growing journal:

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_view_server.py \
  --journal /tmp/missipy_cells.jsonl \
  --port 8766 \
  --tail
```

## Boundary

This is a Phase 10 read-only local browser view. It does not replace VisPy; it
is the browser/mobile-window path that consumes the same journal contract.
