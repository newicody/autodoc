# 0100-controlproxy_microkernel_direction_audit

This patch fixes the architecture direction issue raised after 0099.

It records that the ControlProxy implementation has two useful but not yet unified lanes:

- current active-route Scheduler-facing handshake lane;
- newer generation/lifecycle/lock/placement lane.

The graph now shows the missing `ControlProxyRouteCoordinator` as planned next integration instead of pretending the lanes are already one path.

Apply with:

```bash
unzip -o /mnt/data/0100-controlproxy_microkernel_direction_audit.zip -d .
python apply_patch_queue.py --patch 0100-controlproxy_microkernel_direction_audit --dry-run
python apply_patch_queue.py --patch 0100-controlproxy_microkernel_direction_audit --commit --push
```
