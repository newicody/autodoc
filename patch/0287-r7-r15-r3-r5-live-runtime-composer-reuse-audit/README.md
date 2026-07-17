# 0287-r7-r15-r3-r5-live-runtime-composer-reuse-audit

Passive, executable source audit for the first tool-bounded live love runtime.

The patch adds no backend and modifies no existing runtime file. It locks the
surfaces that must be reused and proves that the following leaf boundaries are
still absent before a live composer can be truthful:

- PostgreSQL DB-API connection and idempotent base-revision seed;
- async OpenVINO E5 to dense-query adapter;
- Qdrant hybrid dense/sparse and projection adapters;
- final tool-bounded composition.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r5-live-runtime-composer-reuse-audit \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r5-live-runtime-composer-reuse-audit \
  --commit \
  --push \
  --allow-dirty
```

Expected commit subject:

```text
r7-r15-r3-r5-live-runtime-composer-reuse-audit
```
