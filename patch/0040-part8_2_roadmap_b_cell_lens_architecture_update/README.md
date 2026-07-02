# 0040 — Part 8.2 Roadmap B Cell Lens Architecture Update

This patch updates project, architecture and code-rule documentation for the
cell-population visualization track.

## Apply

```bash
python apply_patch_queue.py --patch 0040-part8_2_roadmap_b_cell_lens_architecture_update --dry-run
python apply_patch_queue.py --patch 0040-part8_2_roadmap_b_cell_lens_architecture_update --commit --push
```

## Scope

- Insert the cell lens into Roadmap B.
- Document lens/lever separation.
- Add supplemental observation rules.
- Place VisPy in Phase 9.
- Place mobile SSE view in Phase 10.
- Keep optimization loop out of scope.

## Out of scope

- No runtime implementation.
- No VisPy dependency.
- No EventBus consumer yet.
- No Scheduler change.
- No server endpoint.
- No DOT/SVG.
