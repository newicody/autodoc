# Manifest — 0088 — ControlProxy Scheduler handler

## Runtime

```text
src/runtime/controlproxy_scheduler_handler.py
```

## Tests

```text
tests/runtime/test_controlproxy_scheduler_handler.py
tests/rules/test_0088_controlproxy_scheduler_handler_rule.py
```

## Documentation

```text
doc/CHANGELOG_0088_CONTROLPROXY_SCHEDULER_HANDLER.md
doc/0088_CODE_RULE_ALIGNMENT.md
doc/manifests/MANIFEST_0088_CHANGED_FILES.md
PHASE0088_TEST_REPORT.md
```

## Kernel-loop boundary

0088 does not change kernel-loop, queue, dispatcher, or component-contract files.

## Boundary

0088 adds an importable Dispatcher handler boundary for the Scheduler-facing
ControlProxy adapter introduced in 0086. It does not add a CLI, daemon, watcher,
OpenRC service, network bridge, mmap resize path, Qdrant path, LLM path, or
OpenVINO path.
