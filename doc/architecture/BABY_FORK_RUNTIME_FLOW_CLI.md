# Baby-fork runtime flow CLI

Status: 0074 end-to-end file-backed flow.

This phase adds one command for the already validated local flow:

```text
baby_fork_report.json
-> runtime projection
-> fake runtime surface
-> recorder journal
-> optional ControlFS desired manifests
-> optional RouteProxy dry-run plan
```

## CLI

```bash
PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
  .var/baby_fork_smoke/baby_fork_report.json \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl \
  --controlfs-root .var/baby_fork_controlfs
```

## Output

The command prints a JSON summary with:

```text
projection counts
fake runtime counts
recorder journal counts
optional ControlFS RouteProxy action counts
```

## What this replaces

Before this phase, the same validation required multiple commands:

```text
export_baby_fork_runtime_projection.py
write_baby_fork_fake_runtime.py
record_fake_runtime.py
write_baby_fork_controlfs_desired.py
baby_fork_routeproxy_plan.py
```

This phase does not remove those tools. It only adds a higher-level orchestrator.

## Non-goals

This phase does not add:

```text
real Scheduler run
RouteProxy daemon
real shared memory
real semaphores
ring buffer
active route creation
revoked route mutation
ZFS requirement
NetworkBridge
HardwareBridge
cluster dispatch
```

## Next phase after this

The next phase can finally start a tiny in-process ring buffer model.

Recommended constraints:

```text
no mmap first
single producer / single consumer
bounded capacity
explicit overflow behavior
same RouteMessage schema at the boundary
```
