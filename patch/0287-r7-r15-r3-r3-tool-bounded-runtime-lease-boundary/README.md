# 0287-r7-r15-r3-r3 — tool-bounded runtime lease boundary

This patch closes the process-local ownership boundary required before the
installed PostgreSQL, Qdrant and OpenVINO runtime can be composed inside the
imported Actions preview CLI.

## Why this unit precedes the first live preview

The r15-r3-r2 provider registry stores Python port objects in the current
process. A server process cannot register those objects for a separate CLI
process. The safe live path is therefore a `tool-bounded` composition created
inside the preview process, with explicit and exact resource cleanup.

## Main effects

- adds `ImportedActionsRuntimeLease` around validated runtime ports;
- adds typed synchronous close hooks referenced by `runtime-close:*` refs;
- binds every lease to its creator process;
- closes tool-owned resources in reverse acquisition order;
- executes every close hook even if one fails;
- makes repeated close calls idempotent through a `replay` receipt;
- preserves factories returning legacy `ImportedActionsRuntimePorts`;
- closes the lease after Scheduler shutdown and on r14/Scheduler failure;
- adds `_r15_runtime_lease` readback to the preview JSON;
- never closes an `externally-managed` runtime.

## Explicit non-effects

This patch does not construct PostgreSQL, Qdrant, OpenVINO, a Scheduler, a
laboratory or a manager. It performs no database/vector write and no GitHub
mutation. It does not claim that a live preview has already succeeded.

## Apply

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r3-tool-bounded-runtime-lease-boundary \
  --commit \
  --push \
  --allow-dirty
```

## Preview readback added

A successful tool-bounded preview will expose:

```json
{
  "_r15_runtime_lease": {
    "schema": "missipy.love.imported_actions_runtime_lease.v1",
    "runtime_ref": "runtime:...",
    "owner_ref": "runtime-owner:...",
    "scheduler_lifecycle": "tool-bounded",
    "close_hook_refs": ["runtime-close:..."],
    "closed": true,
    "close_receipt": {
      "action": "closed",
      "valid": true
    }
  }
}
```

Executable callbacks are never serialized.

## Validation performed by the patch builder

- `git diff --check`: passed;
- `git apply --check` on the reconstructed r15-r3-r2-r2 base: passed;
- Python compilation: passed;
- 14 focused contract/lifecycle/rule tests: passed;
- Scheduler failure at r14 completion is not silenced;
- Graphviz DOT parsing: passed;
- no `.pyc`, SVG, secret value, or binary payload included.

The full repository rule and global suites are delegated to
`apply_patch_queue.py` on the real checkout.

## Next unit

```text
0287-r7-r15-r3-r3-r1
canonical tool-bounded live runtime composer and first preview
```

It will acquire the existing PostgreSQL authority, OpenVINO E5-384 pipeline,
Qdrant `autodoc_context_current` adapter and canonical Scheduler in the same CLI
process, attach their close hooks to this lease, then run a real `RUN_ID` in
preview-only mode.
