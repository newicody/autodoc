# 0128-vector_indexing_job_plan

Adds a pure `VectorIndexingJobPlan` layer that prepares Scheduler-addressable E5/OpenVINO embedding jobs and Qdrant projection jobs without executing either backend.

Key boundaries:

- Scheduler remains the orchestrator of vector indexing jobs.
- `/dev/shm` route frames are the multitask data-plane interface and future grid seam.
- SQLContextStore is durable context authority.
- E5/OpenVINO is embedding only behind adapter.
- Qdrant is projection/recall only and does not decide.
- EventBus observes statistics and paths, not payloads.
- GitHub exchanges artifacts only.
- Specialist identity stays payload/filter metadata, not per-specialist collections.

Apply:

```bash
python apply_patch_queue.py --patch 0128-vector_indexing_job_plan --dry-run
python apply_patch_queue.py --patch 0128-vector_indexing_job_plan --commit --push
```
