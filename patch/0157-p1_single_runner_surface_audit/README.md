# 0157 — P1 single runner surface audit

Audit-only patch.

Decision: reuse `tools/run_local_artifact_vector_indexing_runner.py` as the P1
single runner base. Do not create a parallel orchestrator, SQL worker,
Scheduler runner, OpenVINO adapter, or Qdrant adapter.

Apply:

```bash
tar -xzf autodoc_patch_0157-p1_single_runner_surface_audit.tar.gz
python apply_patch_queue.py --patch 0157-p1_single_runner_surface_audit --dry-run
python apply_patch_queue.py --patch 0157-p1_single_runner_surface_audit --commit --push --allow-dirty
```
