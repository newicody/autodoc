# 0168 — GitHub Actions artifact fetch once

## Decision

0168 adds the read-only GitHub Actions artifact fetch step. GitHub Actions
artifacts remain the source system. The local server reads workflow runs and
artifacts, downloads matching artifact ZIP files, extracts them into server-side
staging, then calls the 0167 server dataset sync tool.

The server dataset configured by 0167 remains the local storage authority. 0168
must not write user attachments into the development repository.

## Boundary

- read-only GitHub Actions artifact fetch
- GitHub Actions artifacts remain the source system
- server dataset configured by 0167
- calls 0167 server dataset sync
- conversion starts only after raw sync
- VisPy observes the sync result through the 0167 event file
- does not publish GitHub results
- no remote mutation
- no SQL/qdrant write

## Runtime order

1. Load the existing server fetch ConfigObj/INI file.
2. Resolve the external idea repository and workflow name.
3. List completed GitHub Actions workflow runs.
4. List artifacts for each selected run.
5. Download matching artifacts by prefix.
6. Extract each artifact safely into server staging.
7. Invoke `tools/run_github_artifact_server_sync_once.py`.
8. Let 0167 write raw files, index, history, conversion queue, and VisPy event.
9. Store a fetch state file so already synced artifacts are skipped.

## Non-goals

0168 does not convert attachments, does not run inference, does not publish
response artifacts to GitHub, and does not mutate Project or issue state.
