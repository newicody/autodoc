# 0052 — Part 10.4 Cell Lens Local Demo Bundle

This patch adds a file-only local demo bundle for the Cell Lens chain.

## Apply

```bash
python apply_patch_queue.py --patch 0052-part10_4_cell_lens_local_demo_bundle --dry-run
python apply_patch_queue.py --patch 0052-part10_4_cell_lens_local_demo_bundle --commit --push
```

## Scope

- Generate a synthetic `missipy.cell.v1` journal.
- Replay-check the journal.
- Write an SSE preview.
- Write a JSON report.
- Add tests and docs.

## Out of scope

- No server.
- No browser launch.
- No renderer.
- No command channel.
- No optimization loop.
