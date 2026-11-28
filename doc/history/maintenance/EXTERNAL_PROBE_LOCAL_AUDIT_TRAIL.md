# External probe local audit trail

Phase 7.17 adds a local JSONL audit trail for external probe operator summaries.

The audit trail records each summary as an append-only local line:

```text
doc/maintenance/source_candidate_external_probe_local_audit.jsonl
```

It also writes a compact report:

```text
doc/maintenance/source_candidate_external_probe_local_audit_report.json
```

## Example

```bash
python tools/source_candidate_external_probe_local_audit_trail_cli.py \
  --summary doc/maintenance/source_candidate_external_probe_operator_summary.json \
  --audit-log doc/maintenance/source_candidate_external_probe_local_audit.jsonl \
  --report doc/maintenance/source_candidate_external_probe_local_audit_report.json
```

The audit trail is local-only and does not inspect external services.
