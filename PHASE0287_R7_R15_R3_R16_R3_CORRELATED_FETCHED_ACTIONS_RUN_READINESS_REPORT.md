# Phase 0287-r7-r15-r3-r16-r3 — Correlated fetched Actions run readiness

## Reuse audit

The repository already contains the full read-only fetch chain:

```text
run_github_actions_artifact_scan_once_live_0272.py
→ run_github_actions_artifact_fetch_once.py
→ run_github_artifact_server_sync_once.py
→ local append-only dataset/state
```

The fetch tool already lists completed workflow runs, downloads matching ZIP
artifacts, extracts them safely, syncs them into the server dataset and
deduplicates each artifact by repository, run ID and artifact ID.

Creating another poller, downloader or state file would duplicate this path.

## Extension

The existing scan result now groups fetched records by workflow run and accepts
one run as `ready` only when it contains exactly one locally available member
for each role:

```text
authoritative_request
copilot_advisory
run_manifest
```

Both legacy names and the current human-readable names are accepted through the
existing identity matcher.

A member is locally available when it was downloaded and synced in the current
scan or skipped because it was already synchronized.

Expired, missing or duplicate members produce a `deferred_runs` entry. They do
not invalidate the fetch itself and do not start local execution.

## Next boundary

The next unit may consume `ready_runs` and invoke the existing imported Actions
closed-loop command one run at a time. This phase performs no laboratory,
Scheduler, SQL, Qdrant or remote publication action.
