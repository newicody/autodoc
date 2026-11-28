# 0069 - Fake runtime recorder ingestion

## Added

- `runtime.fake_runtime_recorder`
- `RuntimeJournalRecord`
- `FakeRuntimeRecorderSummary`
- ingestion from fake runtime JSONL files
- CLI tool `tools/record_fake_runtime.py`
- documentation for fake recorder ingestion
- tests for baby-fork fake runtime -> journal path
- rule tests locking no-real-runtime scope

## Not added

- No real shared memory.
- No semaphores.
- No ring buffer.
- No Recorder daemon.
- No Scheduler wiring.
- No RouteProxy daemon.
- No ControlFS mutation.
- No ZFS requirement.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
