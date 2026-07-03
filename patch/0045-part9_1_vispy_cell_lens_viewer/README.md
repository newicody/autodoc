# 0045 — Part 9.1 VisPy Cell Lens Viewer

This patch adds the first desktop viewer boundary for the cell lens.

## Apply

```bash
python apply_patch_queue.py --patch 0045-part9_1_vispy_cell_lens_viewer --dry-run
python apply_patch_queue.py --patch 0045-part9_1_vispy_cell_lens_viewer --commit --push
```

## Scope

- Add renderer-neutral health mapping.
- Add renderer-neutral cell projection.
- Add optional VisPy desktop viewer tool.
- Add tests that do not require VisPy.
- Keep VisPy confined to the tool boundary.

## Out of scope

- No real observation recorder consumer.
- No mobile SSE.
- No command path.
- No optimization loop.
