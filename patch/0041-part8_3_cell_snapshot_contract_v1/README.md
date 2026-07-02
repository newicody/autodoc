# 0041 — Part 8.3 Cell Snapshot Contract v1

This patch adds the immutable `missipy.cell.v1` observation contract.

## Apply

```bash
python apply_patch_queue.py --patch 0041-part8_3_cell_snapshot_contract_v1 --dry-run
python apply_patch_queue.py --patch 0041-part8_3_cell_snapshot_contract_v1 --commit --push
```

## Scope

- Add `CellSnapshot`.
- Add schema constant `missipy.cell.v1`.
- Add JSON serialization/deserialization.
- Add validation.
- Add contract docs and rule tests.

## Out of scope

- No EventBus consumer.
- No recorder writer.
- No journal tail/replay reader.
- No VisPy.
- No mobile SSE.
- No optimization loop.
