# External probe local replay

Phase 7.18 adds a local replay report for the external probe audit trail.

The replay reads:

```text
doc/maintenance/source_candidate_external_probe_local_audit.jsonl
```

and writes:

```text
doc/maintenance/source_candidate_external_probe_local_replay_report.json
```

## Example

```bash
python tools/source_candidate_external_probe_local_replay_cli.py \
  --audit-log doc/maintenance/source_candidate_external_probe_local_audit.jsonl \
  --report doc/maintenance/source_candidate_external_probe_local_replay_report.json
```

## Latest events only

```bash
python tools/source_candidate_external_probe_local_replay_cli.py \
  --audit-log doc/maintenance/source_candidate_external_probe_local_audit.jsonl \
  --report doc/maintenance/source_candidate_external_probe_local_replay_report.json \
  --limit 10
```

The replay is local-only and does not inspect external services.
