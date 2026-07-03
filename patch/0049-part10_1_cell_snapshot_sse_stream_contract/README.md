# 0049 — Part 10.1 Cell Snapshot SSE Stream Contract

This patch defines the read-only SSE text contract for future local browser/mobile viewing.

## Apply

```bash
python apply_patch_queue.py --patch 0049-part10_1_cell_snapshot_sse_stream_contract --dry-run
python apply_patch_queue.py --patch 0049-part10_1_cell_snapshot_sse_stream_contract --commit --push
```

## Scope

- Add `missipy.cell_snapshot_sse.v1`.
- Convert `missipy.cell.v1` snapshots to SSE text events.
- Add journal-to-SSE dry-run CLI.
- Add tests and docs.

## Out of scope

- No local server.
- No endpoint.
- No browser UI.
- No command channel.
- No optimization loop.
