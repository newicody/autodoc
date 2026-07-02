# 0044 — Part 8.6 Synthetic Cell Population Generator

This patch adds a deterministic synthetic generator for `missipy.cell.v1`
snapshots.

## Apply

```bash
python apply_patch_queue.py --patch 0044-part8_6_synthetic_cell_population_generator --dry-run
python apply_patch_queue.py --patch 0044-part8_6_synthetic_cell_population_generator --commit --push
```

## Scope

- Add deterministic synthetic profiles and seeds.
- Add synthetic `missipy.cell.v1` snapshot generator.
- Add CLI that writes a JSONL journal through the existing journal writer.
- Add tests and docs.

## Out of scope

- No real EventBus consumer.
- No recorder stream integration.
- No VisPy.
- No mobile SSE.
- No optimization loop.
