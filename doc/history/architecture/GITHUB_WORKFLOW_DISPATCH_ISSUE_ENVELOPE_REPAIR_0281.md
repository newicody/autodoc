# GitHub workflow_dispatch Issue envelope repair — 0281-r4-r1

The controlled workflow now inserts a strict normalization boundary between the
synthetic dispatch event and the existing authoritative-request builder.

The adapter accepts the selected Issue JSON and the synthetic event. It accepts
an embedded Issue object, a JSON-encoded Issue object, or repairs a missing
Issue field from the already-fetched selected Issue payload. A different Issue
number is always rejected.

The existing `build_autodoc_authoritative_request.py` remains the sole
authoritative artifact builder.

```text
newicody/autodoc: modification required
newicody/projects: deployed workflow modification required
projects_repository_change_required: true
```

No new GitHub permission, remote mutation, Scheduler path, SQL write or Qdrant
write is introduced.
