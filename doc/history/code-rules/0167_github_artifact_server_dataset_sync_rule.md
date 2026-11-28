# Code rule — 0167 GitHub artifact server dataset sync

## Rule

Do not store user artifacts in Git.

Use the server dataset configured by ConfigObj.

Queue conversion only after complete raw sync.

Do not create a parallel artifact system.

## Required behavior

- Treat GitHub Actions artifacts as the source artifact system.
- Copy fetched artifacts and attachments into the configured server dataset.
- Record provenance, hash, size and raw dataset reference.
- Emit a VisPy observation event for sync status.
- Queue only unprocessed items after raw sync completes.

## Forbidden behavior

- Do not store photos, audio, video, PDFs, archives or user text artifacts in the development repository.
- Do not call GitHub API in 0167.
- Do not perform remote mutation.
- Do not write SQL.
- Do not write Qdrant.
- Do not run inference.
- Do not manage fcron or OpenRC.
