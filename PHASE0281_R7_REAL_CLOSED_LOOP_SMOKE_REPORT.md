# Phase 0281-r7-r1 report

The rejected manual `--run-root` design is removed. The smoke now loads the
existing fetch INI, requires a ready r3 run-group and reads only imported files
from `server_dataset.raw`.

```text
code_rule_review: done
live_path_status: transition
existing_fetch_config_reused: true
existing_server_dataset_reused: true
new_storage_section_required: false
manual_download_path_allowed: false
existing_scheduler_reused: true
scheduler_modified: false
laboratory_scheduler_added: false
github_mutation_added: false
projects_repository_change_required: false
```

```text
newicody/projects: no Git-tracked modification required
```

```text
forward_correction_of_committed_r7: true
old_manual_run_root_removed: true
patch_id: 0281-r7-r1-real-closed-loop-dataset-boundary
```
