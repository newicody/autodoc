# Cell Lens All View Launch Profiles

```text
schema: missipy.cell_lens_all_view_launch_profiles.v1
```

This tool prints local read-only launch profiles for all current Cell Lens views.

It does not start anything by itself.

## Modes

### VisPy desktop

```bash
PYTHONPATH=src:. VISPY_APP=pyqt6 QT_QPA_PLATFORM=wayland python tools/visualize_cell_population_vispy.py \
  --journal .var/cell_lens_demo/cells.jsonl
```

Use `QT_QPA_PLATFORM=wayland` on a native Wayland session.

### browser Canvas

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_view_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8766
```

Open:

```text
http://127.0.0.1:8766/view.html
```

### browser health Canvas

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_health_view_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8767
```

Open:

```text
http://127.0.0.1:8767/health-view.html
```

### SSE stream

```bash
PYTHONPATH=src:. python tools/cell_snapshot_sse_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8765
```

Inspect:

```text
http://127.0.0.1:8765/cells.sse
```

## Rule

All launch profiles are read-only viewing profiles.

They consume the same `missipy.cell.v1` journal and do not introduce an action
surface.
