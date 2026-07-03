# Cell Lens Local UI Runbook

This runbook gives the repeatable local commands for the Cell Lens UI.

## 1. Build demo data

```bash
PYTHONPATH=src:. python tools/cell_lens_local_demo_bundle.py \
  --output-dir .var/cell_lens_demo \
  --population-size 32 \
  --tick-count 20 \
  --seed 42 \
  --sse-limit 20
```

Expected output:

```text
.var/cell_lens_demo/cells.jsonl
.var/cell_lens_demo/cells.sse
.var/cell_lens_demo/report.json
```

## 2. VisPy desktop

On native Wayland:

```bash
VISPY_APP=pyqt6 QT_QPA_PLATFORM=wayland PYTHONPATH=src:. python tools/visualize_cell_population_vispy.py \
  --journal .var/cell_lens_demo/cells.jsonl
```

On XCB/XWayland, the Qt XCB plugin dependencies must be installed before using:

```bash
VISPY_APP=pyqt6 QT_QPA_PLATFORM=xcb PYTHONPATH=src:. python tools/visualize_cell_population_vispy.py \
  --journal .var/cell_lens_demo/cells.jsonl
```

## 3. SSE stream

```bash
PYTHONPATH=src:. python tools/cell_snapshot_sse_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8765
```

Open:

```text
http://127.0.0.1:8765/cells.sse
```

## 4. Browser Canvas

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_view_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8766
```

Open:

```text
http://127.0.0.1:8766/view.html
```

## 5. Browser health Canvas

```bash
PYTHONPATH=src:. python tools/cell_snapshot_browser_health_view_server.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --port 8767
```

Open:

```text
http://127.0.0.1:8767/health-view.html
```

## 6. Print all launch profiles

```bash
PYTHONPATH=src:. python tools/cell_lens_all_view_launch_profiles.py \
  --journal .var/cell_lens_demo/cells.jsonl \
  --qt-platform wayland \
  --shell
```

## Boundary

Every command in this runbook is read-only with respect to the system being
observed.

The only written files are local demo artifacts and reports.
