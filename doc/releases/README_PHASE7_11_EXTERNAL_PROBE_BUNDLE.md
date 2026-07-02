# Phase 7.11 — External Probe Bundle

Phase 7.11 adds a local external probe bundle.

The bundle groups the local read-only probe artifacts into a deterministic
directory:

```text
manifest.json
operator_external_review_report.json
read_only_external_probe_request.json
read_only_external_probe_result.json
```

The phase remains local-only. It does not contact external services.
