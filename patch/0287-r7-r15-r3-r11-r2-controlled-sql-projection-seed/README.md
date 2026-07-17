# 0287-r7-r15-r3-r11-r2-controlled-sql-projection-seed

SQL-only, preview-first and idempotent bootstrap for the first live projection
probe. The installed base revision is preserved as an immutable parent; the
seed creates one authority object and one accepted child revision.

## Dry-run

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-r2-controlled-sql-projection-seed \
  --dry-run \
  --allow-dirty
```

## Commit and push

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-r2-controlled-sql-projection-seed \
  --commit \
  --push \
  --allow-dirty
```

## Preview after integration

```bash
python tools/seed_love_live_projection_sql_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:love-controlled-sql-seed-preview \
  --format json |
tee /tmp/love-controlled-sql-seed-preview.json
```

The preview performs SQL readback only. Execution requires the exact plan
digest, operator approval, and
`AUTODOC_SQL_PROJECTION_SEED_WRITE_ALLOWED=true`.
