# 0111-r3-route_dev_shm_runtime_namespace_error_fix

Correctif minimal pour l'état 0111 dirty : le comportement symlink/namespace est bon, mais le test runtime attend que le message d'erreur contienne `namespace root`.

Ce patch ne change que le libellé d'erreur dans `src/runtime/route_dev_shm_runtime.py`.

Application :

```bash
unzip -o /mnt/data/0111-r3-route_dev_shm_runtime_namespace_error_fix.zip -d .
python apply_patch_queue.py --patch 0111-r3-route_dev_shm_runtime_namespace_error_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0111-r3-route_dev_shm_runtime_namespace_error_fix --allow-dirty --commit --push
```
