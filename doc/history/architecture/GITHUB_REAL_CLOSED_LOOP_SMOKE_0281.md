# GitHub real closed-loop smoke — 0281-r7-r1

The smoke consumes the existing fetch INI and resolves one ready r3 run-group
from `server_dataset.index`. Artifact bytes are read exclusively from
`server_dataset.raw`, using the recorded relative paths, sizes and SHA-256
digests.

The staging path stored in the run-group report is not trusted or used.
Manual downloads and Git checkout paths are not accepted.

```text
ready imported run-group
-> verified immutable raw members
-> r2/0275 intake
-> operator promote
-> r5 advisory projection
-> existing Scheduler
-> 0274 fake laboratory closure
-> r6 publication preview and plan
```

Outputs are written under:

```text
server_dataset.index/github_closed_loop_0281/<repository>/<run-id>/
```

```text
newicody/autodoc: modification required
newicody/projects: no Git-tracked modification required
projects_repository_change_required: false
fetch_ini_change_required: false
new_storage_section_required: false
existing_server_dataset_reused: true
```

## Forward correction from committed r7

The first committed r7 accepted a manual `--run-root`. The r7-r1 correction
removes that CLI and resolves a ready run exclusively through the existing
fetch INI, `ServerDatasetLayout`, the r3 run-group report, and immutable raw
dataset members.
