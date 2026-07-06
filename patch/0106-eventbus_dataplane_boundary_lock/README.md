# 0106-eventbus_dataplane_boundary_lock

Locks the boundary between EventBus observation and the route mmap/eventfd data
plane.

This patch is documentation, architecture graph and rule tests only. It adds no
runtime code.

Apply with:

```bash
unzip -o /mnt/data/0106-eventbus_dataplane_boundary_lock.zip -d .
python apply_patch_queue.py --patch 0106-eventbus_dataplane_boundary_lock --dry-run
python apply_patch_queue.py --patch 0106-eventbus_dataplane_boundary_lock --commit --push
```
