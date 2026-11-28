# 0167 — GitHub artifact server dataset sync

## Decision

GitHub Actions artifacts remain the source system. Autodoc does not create a
parallel artifact system inside the development repository.

The server fetches/synchronizes GitHub Actions artifacts into the server dataset
configured by ConfigObj. Raw sync completes before conversion starts.

## Server dataset

The dataset contains:

- raw artifacts and attachments
- index records
- append-only history
- conversion queue
- converted outputs
- VisPy observation event files

This is server data, not Git repository data.

## Attachment support

Attachments can be photo/image, audio, video, PDF, archive, text or binary. They
are stored under the raw dataset first, with provenance, hash, size and kind.
Only after the raw sync is complete are unprocessed attachments queued for
conversion.

## VisPy

The sync step emits a VisPy observation event with counts and status so the UI can
show how many artifacts and files were recovered, queued and prepared.

## Boundary

- GitHub Actions artifacts remain the source system
- server dataset configured by ConfigObj
- raw sync completes before conversion
- VisPy observation event emitted
- do not store user artifacts in the development repository
- no GitHub API call in this phase
- no remote mutation
- no SQL/qdrant write
- no inference execution
