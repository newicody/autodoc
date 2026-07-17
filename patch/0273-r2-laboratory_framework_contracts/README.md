# 0273-r2 — Laboratory framework contracts

Adds immutable `missipy.laboratory.v1` contracts and an inactive binding plan
for the existing Scheduler-owned registry.

No provider or backend is activated.

```bash
python apply_patch_queue.py \
  --patch 0273-r2-laboratory_framework_contracts \
  --dry-run \
  --allow-dirty
```
