# 0111-route_dev_shm_runtime_mountinfo_fix

Correctif minimal pour 0111.

Le runtime `/dev/shm` ne doit pas demander des permissions utilisateur supplémentaires pendant les tests. Quand `require_tmpfs=False`, la vérification tmpfs est volontairement sautée. Quand `require_tmpfs=True`, les entrées `/proc/mounts` inaccessibles sont ignorées au lieu de propager `PermissionError`.

Application sur état dirty après l'échec 0111 :

```bash
python apply_patch_queue.py --patch 0111-route_dev_shm_runtime_mountinfo_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0111-route_dev_shm_runtime_mountinfo_fix --allow-dirty --commit --push
```
