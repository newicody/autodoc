# 0287-r7-r15-r3-r10-qdrant-named-collection-control

Controlled creation/readiness for the canonical physical hybrid Qdrant
collection.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-qdrant-named-collection-control \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-qdrant-named-collection-control \
  --commit \
  --push \
  --allow-dirty
```

## Merge into the local `[qdrant]` section

```ini
physical_collection = autodoc_context_e5_384_hybrid_v1
collection_alias = autodoc_context_hybrid_current
dense_vector_name = dense_e5_v1
sparse_vector_name = sparse_lexical_v1
```

Keep the existing legacy line:

```ini
collection = autodoc_context_current
```

## Read-only preview

```bash
python tools/control_love_qdrant_named_collection_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:qdrant-r10-preview \
  --format json |
tee /tmp/love-qdrant-r10-preview.json
```

Creation remains a separate explicitly approved operation.
