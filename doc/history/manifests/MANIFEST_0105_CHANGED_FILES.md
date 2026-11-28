# Manifest 0105 — Scheduler priority/admission lock

Changed files:

```text
doc/architecture/SCHEDULER_PRIORITY_ADMISSION_0105.md
doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0105.md
doc/docs/architecture/runtime/95_scheduler_priority_admission.dot
doc/CHANGELOG_0105_SCHEDULER_PRIORITY_ADMISSION_LOCK.md
doc/manifests/MANIFEST_0105_CHANGED_FILES.md
tests/rules/test_scheduler_priority_admission_0105_rule.py
PHASE0105_TEST_REPORT.md
```

This phase intentionally does not change kernel loop, dispatcher, queue,
policy, handler, EventBus, Component contract, or ControlProxy runtime files.
