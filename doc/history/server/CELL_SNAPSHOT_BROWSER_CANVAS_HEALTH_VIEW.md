# Cell Snapshot Browser Canvas Health View

This tool serves a local read-only browser Canvas health view for the Cell Lens.

```text
host: 127.0.0.1
view: /health-view.html
stream: /cells.sse
health: /health
```

## Purpose

```text
same missipy.cell.v1 journal
→ SSE stream
→ browser EventSource
→ Canvas drawing
→ health/status legend
```

The browser health view is a window over the journal. It is not a source of
truth.

## Health mapping

The page estimates status from `source_class`, `age`, and lifecycle state:

```text
healthy
late
degraded
terminal
```

This is a display hint only. It does not write back to the system.

## Read-only rule

No command channel.

The page only opens an EventSource to `/cells.sse` and draws the latest snapshot
per cell.

## Usage

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_health_view_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8767
```

Then open:

```text
http://127.0.0.1:8767/health-view.html
```

## Boundary

This is a Phase 10 local browser view. It keeps the browser as a read-only
window over the same journal contract.
