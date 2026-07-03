# 0054 — Part 10.6 Browser Canvas Health View

This patch adds a local read-only browser Canvas health view.

## Apply

```bash
python apply_patch_queue.py --patch 0054-part10_6_browser_canvas_health_view --dry-run
python apply_patch_queue.py --patch 0054-part10_6_browser_canvas_health_view --commit --push
```

## Scope

- Add `/health-view.html` local browser view.
- Read the existing `/cells.sse` stream.
- Draw cells by health/status.
- Show status counts and legend.
- Add tests and docs.

## Out of scope

- No command channel.
- No remote exposure.
- No mobile source of truth.
- No optimization loop.
