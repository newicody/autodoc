# 0053 — Part 10.5 Cell Lens Local Launch Profiles

This patch adds a helper that prints repeatable local read-only launch profiles.

## Apply

```bash
python apply_patch_queue.py --patch 0053-part10_5_cell_lens_local_launch_profiles --dry-run
python apply_patch_queue.py --patch 0053-part10_5_cell_lens_local_launch_profiles --commit --push
```

## Scope

- Add VisPy desktop launch profile.
- Add browser Canvas launch profile.
- Add SSE stream launch profile.
- Detect Wayland/XCB Qt platform preference.
- Add tests and docs.

## Out of scope

- No server implementation.
- No renderer implementation.
- No command channel.
- No dependency.
