# 0229-r3 — EventBus supervision reuse findings triage

This patch refines the 0229 triage tool after the real 0228/0229 report showed two runtime-review findings that are the forbidden regex declarations inside the audit tool itself.

Those findings are not runtime behavior. They are classified as `allowed_audit_self_pattern` only when they come from `tools/audit_eventbus_supervision_reuse_0228.py` and the matched evidence is a raw regex literal.

Expected local result for the reported case:

```text
triaged=True extracted=5 allowed_doc_test_trace=3 allowed_audit_self_pattern=2 runtime_review_required=0 may_resume=True
```

Authority boundary remains unchanged: read-only report triage; no Scheduler.run, no new EventBus, no proxy/SHM/policy/data mutation.
