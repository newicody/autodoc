# 0055 — Part 10.7 Cell Lens All View Launch Profiles

This patch adds a helper that prints all current local read-only launch profiles.

## Apply

```bash
python apply_patch_queue.py --patch 0055-part10_7_cell_lens_all_view_launch_profiles --dry-run
python apply_patch_queue.py --patch 0055-part10_7_cell_lens_all_view_launch_profiles --commit --push
```

## Scope

- Add VisPy desktop profile.
- Add browser Canvas profile.
- Add browser health Canvas profile.
- Add SSE stream profile.
- Keep all profiles read-only.

## Out of scope

- No new server implementation.
- No renderer implementation.
- No command channel.
- No dependency.
