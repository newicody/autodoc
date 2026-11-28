# Phase 7 Freeze + Handoff Contract

Phase 7.20 freezes the completed Part 7 local boundary.

The handoff contract records:

```text
local source of truth
no external service calls allowed
no remote mutation allowed
no Scheduler execution allowed
documentation SVG policy required
operator confirmation required
```

## Build without closure report

```bash
python tools/source_candidate_phase7_handoff_contract_cli.py \
  --output doc/maintenance/source_candidate_phase7_handoff_contract.json
```

## Build from closure report

```bash
python tools/source_candidate_phase7_handoff_contract_cli.py \
  --closure-report doc/maintenance/source_candidate_phase7_closure_report.json \
  --output doc/maintenance/source_candidate_phase7_handoff_contract.json
```

## Part 8 candidates

```text
github_read_only_import_prototype
local_document_context_ingestion
retrieval_evaluation_set
operator_feedback_loop
```

The contract does not open any capability by itself. It only records what is
still closed at the end of Part 7.
