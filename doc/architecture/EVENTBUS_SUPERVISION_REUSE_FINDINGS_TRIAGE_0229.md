# 0229 — EventBus supervision reuse findings triage

## Purpose

Patch 0228 added a read-only reuse audit before resuming functional supervision work. A summary can report that EventBus, Scheduler, passive supervision and runtime/data surfaces exist, while also reporting `forbidden_runtime_evidence_count`.

Patch 0229 makes that result actionable without starting runtime implementation.

It classifies forbidden evidence into:

```text
allowed_doc_test_trace
runtime_review_required
review_required
unknown_review_required
```

Only findings in runtime/review categories block the next functional patch.

## Canonical next path

The desired functional path remains:

```text
EventBus -> PassiveSupervisorSink -> CellularState

Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
```

The triage tool does not implement that path. It only decides whether the repository is ready for the next implementation patch.

## Authority boundary

The triage is read-only over a JSON report. It must not:

```text
call Scheduler.run()
create a new EventBus
control RouteProxy or ControlProxy
read or mutate raw SHM
make policy decisions
write SQL
write Qdrant
mutate GitHub
turn events.jsonl into the live runtime path
```

## Expected usage

```bash
python tools/triage_eventbus_supervision_reuse_findings_0229.py \
  --report .var/reports/eventbus_supervision_reuse_0228.json \
  --output .var/reports/eventbus_supervision_reuse_findings_triage_0229.json \
  --format summary
```

If `may_resume_functional_supervision_patch` is true, the next patch may implement the direct sink by reusing existing surfaces. If it is false, the runtime review findings must be inspected first.


## 0229-r3 refinement

Evidence that comes from the forbidden-pattern declarations inside `tools/audit_eventbus_supervision_reuse_0228.py` is classified as `allowed_audit_self_pattern` when the matched text is the raw regex literal itself. This prevents the audit tool from blocking functional resumption because it contains the patterns it is designed to detect.
