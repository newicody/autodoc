# Changelog — Part 9.1 VisPy Cell Lens Viewer

## Added

- `src/visualization/cell_lens_health.py`
- `src/visualization/cell_lens_projection.py`
- `tools/visualize_cell_population_vispy.py`
- Viewer documentation and tests.

## Behavior

The viewer reads the JSONL journal through replay/tail readers and projects the
latest snapshot per cell into renderer-neutral points.

VisPy is imported only when the tool runs.

## Not changed

- No Scheduler path.
- No EventBus subscription.
- No recorder core modification.
- No server or mobile endpoint.
