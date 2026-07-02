# External probe artifact index

Phase 7.15 adds a local index for SourceCandidate external probe bundles.

The index scans a local directory for bundle manifests with schema:

```text
missipy.source_candidate.external_probe_bundle.v1
```

It writes a JSON index containing repository, read-only status, external-call
status and artifact counts.

## Example

```bash
python tools/source_candidate_external_probe_artifact_index_cli.py \
  --root . \
  --scan-root /tmp/source_candidate_external_probe_bundles \
  --output doc/maintenance/source_candidate_external_probe_artifact_index.json
```

## JSON output

```bash
python tools/source_candidate_external_probe_artifact_index_cli.py \
  --root . \
  --scan-root /tmp/source_candidate_external_probe_bundles \
  --output doc/maintenance/source_candidate_external_probe_artifact_index.json \
  --json
```

The indexer is local-only and does not inspect external services.
