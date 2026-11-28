# GitHub dual-artifact Actions workflow — 0275-r3

The workflow always produces the authoritative request. Copilot advisory is
optional and enabled only through repository configuration. It runs in
non-interactive CLI mode with write and shell tools denied, then writes a
separate advisory file. A third manifest links both files by digest.

Permissions are read-only. The workflow performs no issue comment, edit, label,
ProjectV2 mutation or Autodoc SQL/Qdrant write. The token is supplied only by an
Actions secret and is never serialized.
