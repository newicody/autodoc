# 0287-r7-r15-r3-r10-r1-qdrant-settings-backward-compatibility

Correctif pour le worktree où r10 est déjà appliqué mais non commité après
l'échec de la suite globale.

Le correctif restaure la compatibilité des anciens appels directs à
`QdrantRuntimeSettings` et touche les 14 artefacts r10 afin que la Patch Queue
commite l'unité complète.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r1-qdrant-settings-backward-compatibility \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r10-r1-qdrant-settings-backward-compatibility \
  --commit \
  --push \
  --allow-dirty
```
