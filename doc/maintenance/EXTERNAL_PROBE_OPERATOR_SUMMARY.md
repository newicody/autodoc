# External probe operator summary

Phase 7.16 adds a local operator summary for external probe artifact indexes.

The summary reads:

```text
source_candidate_external_probe_artifact_index.json
```

and writes:

```text
source_candidate_external_probe_operator_summary.json
```

## Example

```bash
python tools/source_candidate_external_probe_operator_summary_cli.py \
  --index doc/maintenance/source_candidate_external_probe_artifact_index.json \
  --output doc/maintenance/source_candidate_external_probe_operator_summary.json
```

## Status meanings

```text
ready   = read-only, no external call already performed, probe allowed
check   = read-only, no external call already performed, probe not allowed
blocked = not read-only or external call already performed
```

The summary is local-only and does not inspect external services.
