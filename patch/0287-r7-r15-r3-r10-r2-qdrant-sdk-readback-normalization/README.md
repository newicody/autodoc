# 0287-r7-r15-r3-r10-r2-qdrant-sdk-readback-normalization

Correctif cumulatif pour le worktree actuel où r10 est déjà appliqué mais non
commité.

Il inclut :

- la compatibilité descendante des cinq nouveaux champs Qdrant de r10-r1 ;
- la normalisation des enums du SDK qdrant-client pour `status`, `distance` et
  `payload_schema.data_type` ;
- les tests de régression correspondants ;
- les 14 fichiers r10 afin que `apply_patch_queue.py` commite l’unité complète.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r2-qdrant-sdk-readback-normalization \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r2-qdrant-sdk-readback-normalization \
  --commit \
  --push \
  --allow-dirty
```

## Readback après intégration

```bash
unset AUTODOC_QDRANT_COLLECTION_MUTATION_ALLOWED

python tools/control_love_qdrant_named_collection_0287.py \
  --config .var/config/love_installed_runtime.ini \
  --policy-decision-id policy:qdrant-r10-r2-readback \
  --format json |
tee /tmp/love-qdrant-r10-r2-readback.json
```

Aucune nouvelle mutation Qdrant n’est requise.
