# 0106-r2 — EventBus / data plane boundary lock

This is a packaging-safe replacement for `0106-eventbus_dataplane_boundary_lock`.

It keeps the same repository changes as 0106 but uses a new patch id so it does
not collide with an already-unzipped `patch/0106-eventbus_dataplane_boundary_lock`
directory in the working tree.

The diff does not create files under `patch/`; it only adds the repository docs,
architecture `.dot`, manifest, rule test and phase report.
