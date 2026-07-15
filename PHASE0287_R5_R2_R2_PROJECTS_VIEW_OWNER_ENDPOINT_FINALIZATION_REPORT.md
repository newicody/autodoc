# Phase 0287-r5-r2-r2 — ProjectV2 endpoint finalization

Status: final corrective deployment procedure.

Two `git apply` patches failed because they reconstructed the 446-line
reconciler from incomplete fixtures. This phase deliberately stops patching
that file by line context.

The endpoint is repaired before patch application by an exact content
substitution that:

- requires exactly one occurrence of the numeric view endpoint;
- replaces only that occurrence with the configured owner login;
- aborts without writing if the expected source is absent or duplicated.

The patch itself modifies only the cumulative installation guide and adds a
regression rule. `apply_patch_queue.py --allow-dirty` then tests and commits the
content-repaired script together with the documentation closure.

Live probes established the required endpoint:

```text
users/58338908/projectsV2/3/views → HTTP 404
users/newicody/projectsV2/3/views → API validation reached
```
