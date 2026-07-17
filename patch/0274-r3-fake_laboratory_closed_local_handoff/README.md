# 0274-r3 — Fake laboratory closed local handoff

Closes the converged r2 result through existing SQL, E5/Qdrant, EventBus,
PassiveSupervisor, Cell Lens and local GitHub-preview surfaces.

```bash
python apply_patch_queue.py \
  --patch 0274-r3-fake_laboratory_closed_local_handoff \
  --dry-run \
  --allow-dirty
```

No Scheduler, orchestrator, bus, registry or remote mutation is added.
