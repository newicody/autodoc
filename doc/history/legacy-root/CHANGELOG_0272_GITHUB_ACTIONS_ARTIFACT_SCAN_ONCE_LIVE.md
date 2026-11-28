# Changelog — 0272-r2

- Added a gated scan-once composition around the existing GitHub Actions artifact fetch and server dataset sync.
- Superseded the 0272-r1 direct issue-client orientation; direct issue scan is not required.
- Aligned the Project example config and fcron command with the new gated scan-once CLI.
- Removed the manual `workflow_dispatch` trigger from the artifact workflow template.
- Kept GitHub GET/download-only, append-only local history and `remote_mutation_allowed=False`.
- Added no dependency, runtime manager, Scheduler modification, SQL write, Qdrant write or SHM change.
