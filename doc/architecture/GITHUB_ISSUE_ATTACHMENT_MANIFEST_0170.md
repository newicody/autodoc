# 0170 — GitHub issue attachment manifest

## Decision

0170 covers photo, audio, video, PDF, archive, and text attachment references.

0170 adds a reference-only manifest for attachments pasted into the external
GitHub idea repository issue body. It supports photo, audio, video, PDF,
archive, and text references, plus binary fallback references.

The manifest records GitHub issue attachment references only. It does not
download the files, does not call the GitHub API, and does not perform remote
mutation. GitHub Actions artifacts remain the source system.

## Flow

The external GitHub Action parses the issue body and writes
`attachment_manifest.json` as a GitHub Actions artifact. The local server then
fetches that artifact and, in the next fetch/download phase, stores real user
files in the configured server dataset before conversion.

## Boundary

- no GitHub API call
- no remote mutation
- no user artifacts in Autodoc repository
- server dataset before conversion
- attachment manifest is metadata only
