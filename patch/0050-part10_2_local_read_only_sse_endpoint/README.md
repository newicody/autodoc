# 0050 — Part 10.2 Local Read-Only SSE Endpoint

This patch adds a local-only read-only SSE endpoint tool for the cell snapshot journal.

## Apply

```bash
python apply_patch_queue.py --patch 0050-part10_2_local_read_only_sse_endpoint --dry-run
python apply_patch_queue.py --patch 0050-part10_2_local_read_only_sse_endpoint --commit --push
```

## Scope

- Add `/cells.sse` local endpoint tool.
- Bind only to `127.0.0.1`.
- Reject write-like HTTP methods.
- Stream the existing `missipy.cell.v1` journal as SSE.
- Add tests and docs.

## Out of scope

- No browser UI.
- No command channel.
- No remote exposure.
- No optimization loop.
