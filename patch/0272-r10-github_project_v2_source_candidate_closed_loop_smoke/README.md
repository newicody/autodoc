# 0272-r10 — ProjectV2 SourceCandidate closed-loop smoke

Closes the current local chain from one immutable r7 operator gate through SQL,
E5, Qdrant projection, refs-only recall and SQL rehydration.

## Base

Apply on top of:

```text
0b338de r9-projectv2-vector-projection-metadata-fix
```

## Reuse

The patch composes existing surfaces only:

```text
r7 gate record
-> r8 durable SQL consumer + readback
-> r8 idempotent replay
-> 0261 query E5 embedding
-> r10 query compatibility gate
-> r9 passage embedding/profile/Qdrant projection
-> 0263 Qdrant recall refs-only
-> SQL rehydrate
-> closed r10 report
```

The r6 handoff and r7 decision remain upstream and are not reimplemented.

## Boundaries

- SQL remains the durable authority.
- E5 query compatibility is checked before any Qdrant write.
- The existing 0261 surface now propagates its already-declared query role instead of always building `passage:` text.
- Passage/query profiles share one `embedding_space_family_ref`.
- Qdrant carries `sql_ref` and is verified through SQL rehydration.
- GitHub mutation remains closed.
- Laboratory selection remains closed.
- `Scheduler.run()`, ControlProxy, RouteProxy and SHM are unchanged.
- No manager, orchestrator, bus or registry is added.
- No non-stdlib dependency is added.
- No generated `.pyc` or `__pycache__` artifact is included.

## Apply

```bash
unzip -o \
  /mnt/data/0272-r10-github_project_v2_source_candidate_closed_loop_smoke.zip

python apply_patch_queue.py \
  --patch 0272-r10-github_project_v2_source_candidate_closed_loop_smoke \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0272-r10-github_project_v2_source_candidate_closed_loop_smoke \
  --commit \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_closed_loop_smoke_0272.py \
  tests/context/test_scheduler_managed_sql_ref_openvino_embedding_query_role_0272.py \
  tests/tools/test_run_github_project_v2_source_candidate_closed_loop_smoke_0272.py
PYTHONPATH=src:. python -m pytest -q
```
