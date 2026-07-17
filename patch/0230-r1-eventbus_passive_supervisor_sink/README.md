# 0230-r1 EventBus Passive Supervisor Sink

Functional resumption patch after 0229 triage reports `may_resume=True`.

This patch updates the existing passive bus supervisor module with
`PassiveSupervisorSink`, a downstream-only sink for canonical EventBus events.
It reuses the 0220 `BusSupervisorEvent`, `event_from_mapping`, and
`build_cellular_snapshot` surfaces.

Apply with:

```bash
python apply_patch_queue.py \
  --patch 0230-r1-eventbus_passive_supervisor_sink \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0230-r1-eventbus_passive_supervisor_sink \
  --commit \
  --push \
  --allow-dirty
```

Boundaries: no new EventBus, no Scheduler.run, no proxy/SHM/policy/data mutation,
no non-stdlib dependency.
