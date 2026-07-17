# 0287-r7-r15-r3-r11-live-qdrant-analysis-projection

Async live projection of one already-persisted SQL authority object through the
existing OpenVINO E5 pipeline and existing qdrant-client membrane.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-live-qdrant-analysis-projection \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r11-live-qdrant-analysis-projection \
  --commit \
  --push \
  --allow-dirty
```

## Boundaries

- one point per call;
- explicit existing Qdrant write gate;
- `passage:` E5 input, 384-d normalized dense vector;
- exact existing sparse lexical builder reused;
- reference-only Qdrant payload;
- no collection/alias mutation;
- no Scheduler, event-loop, PostgreSQL or OpenVINO construction.
