# 0287-r7-r15-r3-r10-r2a-qdrant-sdk-readback-normalization-incremental

Correctif strictement incrémental pour un worktree où `r10-r1` est déjà présent.

Il ne réapplique pas les champs de compatibilité. Il ajoute uniquement :

- la normalisation des enums du SDK Qdrant ;
- les tests de régression du readback ;
- la documentation r10-r2 correspondante.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r2a-qdrant-sdk-readback-normalization-incremental \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r2a-qdrant-sdk-readback-normalization-incremental \
  --commit \
  --push \
  --allow-dirty
```

## Readback

```bash
unset AUTODOC_QDRANT_COLLECTION_MUTATION_ALLOWED

python tools/control_love_qdrant_named_collection_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:qdrant-r10-r2a-readback \
  --format json |
tee /tmp/love-qdrant-r10-r2a-readback.json
```
