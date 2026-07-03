# 0051 — Part 10.3 Browser Canvas Read-Only Cell View

This patch adds a local browser Canvas view that consumes the existing cell snapshot SSE stream.

## Apply

```bash
python apply_patch_queue.py --patch 0051-part10_3_browser_canvas_read_only_cell_view --dry-run
python apply_patch_queue.py --patch 0051-part10_3_browser_canvas_read_only_cell_view --commit --push
```

## Scope

- Add local read-only browser view tool.
- Serve `/view.html`, `/cells.sse`, and `/health`.
- Draw latest cell snapshots on Canvas.
- Bind only to `127.0.0.1`.
- Add tests and docs.

## Out of scope

- No command channel.
- No remote exposure.
- No mobile source of truth.
- No optimization loop.
