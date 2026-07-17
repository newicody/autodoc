# 0272-r9-r2 — ProjectV2 vector projection empty metadata fix

Corrective patch for the r9 working tree after the full repository suite exposed
an empty optional `model_path` metadata value.

The existing `OpenVINOEmbeddingVector` contract correctly rejects every empty
metadata value.  This patch does **not** weaken that contract.  Instead, the r9
composition removes optional empty producer metadata before handing the
embedding report to the existing 0262 projection builder.

## Expected base state

Apply after `0272-r9-r1-github_project_v2_source_candidate_vector_projection_clean`
has been applied but not committed because the full test suite stopped on:

```text
ValueError: metadata value must not be empty
```

The fix modifies the already-present r9 source, focused test, changelog and test
report.  It does not re-add the complete r9 patch.

## Boundaries

- the strict OpenVINO metadata contract is unchanged;
- no empty sentinel or invented model path is introduced;
- SQL remains the durable authority;
- Qdrant remains projection/recall only;
- no laboratory execution is opened;
- no GitHub remote mutation is opened;
- `Scheduler.run()`, ControlProxy, RouteProxy and SHM are unchanged;
- no non-stdlib dependency is added;
- no generated or binary artifact is included.

## Apply

```bash
unzip -o /mnt/data/0272-r9-r2-projectv2_vector_projection_empty_metadata_fix.zip

python apply_patch_queue.py \
  --patch 0272-r9-r2-projectv2_vector_projection_empty_metadata_fix \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0272-r9-r2-projectv2_vector_projection_empty_metadata_fix \
  --commit \
  --allow-dirty
```

## Focused validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_vector_projection_0272.py \
  tests/tools/test_project_github_project_v2_source_candidate_vector_0272.py
```
