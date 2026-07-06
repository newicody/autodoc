# 0111-r2 — route_dev_shm_runtime mountinfo fix

Corrects the 0111 `/dev/shm` runtime boundary helper after full-suite validation found that `_path_is_tmpfs()` could raise `PermissionError` while resolving unrelated mount points such as `/sys/kernel/debug/tracing`.

The fix is intentionally narrow:

- `require_tmpfs=False` no longer scans `/proc/mounts`.
- `_path_is_tmpfs()` treats inaccessible mount points as non-matching mount points.
- No Scheduler, Dispatcher, PolicyEngine, PriorityQueue, EventBus, handler, or RouteRuntimeManager changes.
- No CLI, daemon, watcher, service, bus, or scheduler-like coordinator.

Apply from the repository root:

```bash
unzip -o /mnt/data/0111-r2-route_dev_shm_runtime_mountinfo_fix.zip -d .
python apply_patch_queue.py --patch 0111-r2-route_dev_shm_runtime_mountinfo_fix --allow-dirty --dry-run
python apply_patch_queue.py --patch 0111-r2-route_dev_shm_runtime_mountinfo_fix --allow-dirty --commit --push
```
