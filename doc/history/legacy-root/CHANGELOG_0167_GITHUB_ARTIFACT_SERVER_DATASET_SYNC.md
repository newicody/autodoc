# Changelog — 0167 GitHub artifact server dataset sync

0167 adds a server-side dataset sync contract for fetched GitHub Actions
artifacts and attachments.

## Added

- server dataset layout contract
- fetched artifact record
- attachment record
- conversion queue record
- ConfigObj-style server fetch config
- sync-once tool for already-fetched local artifact directories
- VisPy observation event output
- tests, rules, docs and manifest

## Boundary

No GitHub API call, no remote mutation, no SQL/qdrant write, no inference
execution, no user artifact storage in Git.
