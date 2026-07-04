# Fake runtime recorder ingestion

Status: P6-prep recorder ingestion.

This phase reads the fake local runtime surface and writes a deterministic recorder journal.

## Input

The fake runtime surface from phase 0068:

```text
<runtime_root>/
  data.index.jsonl
  event.bus.jsonl
  context.bus.jsonl
  routes/<route_id>/messages.jsonl
```

## Output

A JSONL journal:

```text
runtime_journal.jsonl
```

Each line is:

```text
missipy.recorder.runtime_journal_record.v1
```

The journal record contains:

```text
record_id
source_surface
message_schema
message_kind
payload_hash
message
```

## Purpose

This phase proves the path:

```text
baby_fork_report.json
-> runtime projection
-> fake runtime surface
-> recorder journal
```

before the real Recorder/ZFS path exists.

## Non-goals

This phase does not add:

```text
real shared memory
real semaphores
ring buffer
Recorder daemon
Scheduler wiring
RouteProxy daemon
ControlFS mutation
ZFS requirement
NetworkBridge
HardwareBridge
cluster dispatch
```

## CLI

```bash
PYTHONPATH=src:. python tools/record_fake_runtime.py \
  .var/baby_fork_fake_runtime \
  .var/baby_fork_fake_runtime/runtime_journal.jsonl
```

## Expected counts for baby-fork projection

For the current baby-fork projection, the expected journal contains:

```text
1 data handle record
2 event records
1 context record
3 route records
7 total records
```

## Next phase after this

The next phase should decide whether to:

```text
add a baby-fork CLI flag that writes fake runtime and recorder journal
create ControlFS desired manifests for baby-fork routes
start designing real shm ring-buffer boundaries
```

The real shm/semaphore implementation should still wait until the file-backed flow is stable.
