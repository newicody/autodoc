# 0272-r9-r1 — ProjectV2 SourceCandidate vector projection (clean patch)

Corrective full replacement for the rejected `0272-r9` bundle.

The original bundle accidentally included generated `__pycache__/*.pyc` entries in
`patch.diff`. This replacement contains the complete r9 source, tests and
documentation changes, with every generated binary artifact removed.

## Base

Apply on top of:

```text
54a1ff8 r8-projectv2-source-candidate-durable-consumer
```

The failed `--dry-run` did not modify tracked source files, so the original r9
must not be applied before this replacement.

## Boundaries

- SQL remains the durable authority.
- OpenVINO/E5 produces the controlled 384-dimensional embedding.
- Qdrant remains projection/recall only and carries `sql_ref`.
- `EmbeddingSpaceProfile` rejects incompatible vector spaces before projection.
- No laboratory execution is opened.
- No GitHub remote mutation is opened.
- `Scheduler.run()`, ControlProxy, RouteProxy and SHM are unchanged.
- No non-stdlib dependency is added.
- No `.pyc` or `__pycache__` artifact is present in the patch.

## Apply

```bash
unzip -o /mnt/data/0272-r9-r1-github_project_v2_source_candidate_vector_projection_clean.zip

python apply_patch_queue.py \
  --patch 0272-r9-r1-github_project_v2_source_candidate_vector_projection_clean \
  --dry-run \
  --allow-dirty

python apply_patch_queue.py \
  --patch 0272-r9-r1-github_project_v2_source_candidate_vector_projection_clean \
  --commit \
  --allow-dirty
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_source_candidate_vector_projection_0272.py \
  tests/tools/test_project_github_project_v2_source_candidate_vector_0272.py
```
