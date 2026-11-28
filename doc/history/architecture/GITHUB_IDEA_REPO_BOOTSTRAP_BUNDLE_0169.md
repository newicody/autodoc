# 0169 — GitHub idea repository bootstrap bundle

## Decision

0169 prepares a local bootstrap bundle for the external idea repository. The
external idea repository is the place where the user creates a ticket, attaches
photos, audio, video, text, PDF, archives, or other context, and asks the server
side system to study the task.

0169 does not create a new artifact system. It reuses 0166 templates so the
external repository can produce GitHub Actions artifacts. GitHub Actions
artifacts remain the source system for the later 0168 fetch cycle.

## Boundary

- reuse 0166 templates
- external idea repository only
- local bootstrap only
- no GitHub API call
- no remote mutation
- no user artifacts in Autodoc repository
- no server dataset write
- no conversion
- no inference
- no SQL/qdrant write

## Operator flow

1. Build a staging bundle from `templates/github`.
2. Review the generated files.
3. Optionally copy them into a local clone of `newicody/autodoc-ideas` with
   `--write --external-repo-root`.
4. Commit and push from the external repository, not from Autodoc.
5. Create or edit an issue to trigger the GitHub Action.
6. The Action creates GitHub Actions artifacts.
7. 0168 fetches those artifacts read-only and passes them to the 0167 dataset
   sync.

## Authority

The Git commit history remains the source of truth for Autodoc code. The
`patch/` directory is historical development trace only. GitHub Actions artifacts remain the source system. Runtime/user artifacts
belong in GitHub Actions artifacts and then in the configured server dataset.
