# Manifest 0100 — ControlProxy micro-kernel direction audit

## Changed files

```text
doc/architecture/CONTROLPROXY_MICROKERNEL_DIRECTION_AUDIT_0100.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0100.md
doc/docs/architecture/runtime/91_controlproxy_microkernel_direction.dot
doc/manifests/MANIFEST_0100_CHANGED_FILES.md
tests/rules/test_controlproxy_microkernel_direction_0100_rule.py
PHASE0100_TEST_REPORT.md
```

## Intent

0100 records that the current graph was too optimistic: it connected the active-route handshake lane and the newer route-generation lane as if a single coordinator already existed.
The implementation has not fully deviated, but the graph must show that the unification is planned rather than current.

## Guardrails

No CLI.
No OpenRC service and no resident daemon.
No watcher.
No Scheduler.run() modification.
No PriorityQueue, Dispatcher, or Component tick contract modification.
No ControlProxy security authority.
No live mmap resize.
No event.bus command path.
No context.bus command path.
