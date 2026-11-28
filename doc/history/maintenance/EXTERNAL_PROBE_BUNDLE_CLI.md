# External probe bundle CLI

Phase 7.12 adds a CLI surface for the local external probe bundle.

The default mode is dry-run: it prints the bundle plan and writes nothing.

## Dry-run

```bash
python tools/source_candidate_external_probe_bundle_cli.py \
  --output-dir /tmp/source_candidate_external_probe_bundle \
  --operator-review-report /path/to/operator_external_review_report.json \
  --probe-request /path/to/read_only_external_probe_request.json \
  --probe-result /path/to/read_only_external_probe_result.json
```

## Apply

```bash
python tools/source_candidate_external_probe_bundle_cli.py \
  --output-dir /tmp/source_candidate_external_probe_bundle \
  --operator-review-report /path/to/operator_external_review_report.json \
  --probe-request /path/to/read_only_external_probe_request.json \
  --probe-result /path/to/read_only_external_probe_result.json \
  --apply
```

The CLI remains local-only.
