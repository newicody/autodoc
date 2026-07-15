# Phase 0287-r7-r1 — Copilot advisory ProjectV2 publication

Status: controlled local publication path complete.

The missing visible advisories were not caused by Copilot field rendering.
The artifact upload was already working, but field projection was not invoked.

This patch adds:

- strict correlation of authoritative request, advisory and dual manifest;
- SHA-256 verification of request and advisory artifacts;
- construction of the existing publication-preview schema;
- local `gh run download` orchestration;
- reuse of `project_copilot_advisory_fields.py`;
- preview-first planning and exact digest confirmation;
- explicit operator approval and the two existing mutation locks;
- a concise runbook copied into `newicody/projects`.

The workflow remains producer-only and cannot self-authorize publication.
Copilot remains non-authoritative.
