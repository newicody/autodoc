# 0171 — GitHub attachment reference fetch

## Decision

0171 adds the server-side pass that resolves GitHub issue attachment references
recorded by the 0170 attachment manifest. The pass reads metadata from a fetched
GitHub Actions artifact, downloads or fixture-resolves the referenced files, and
stores the raw bytes in the configured server dataset.

This is GitHub issue attachment references only. It does not add user artifacts
to the Autodoc repository.

## Boundary

- GitHub issue attachment references only
- raw files go to the configured server dataset
- conversion is queued only after attachment fetch completes
- no user artifacts in Autodoc repository
- no remote mutation
- no SQL/qdrant write
- no inference execution
- VisPy observation event is emitted after fetch

## Runtime position

GitHub Actions artifact fetch produces `attachment_manifest.json`. 0171 resolves
that manifest into raw dataset files, index/history records, conversion queue
records, and a VisPy observation event. Conversion workers consume the queue
later; 0171 does not convert files directly.
