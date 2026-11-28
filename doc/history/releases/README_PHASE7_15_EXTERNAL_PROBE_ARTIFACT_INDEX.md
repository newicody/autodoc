# Phase 7.15 — External Probe Artifact Index

Phase 7.15 adds a local artifact index for external probe bundles.

It discovers local `manifest.json` files with schema
`missipy.source_candidate.external_probe_bundle.v1`, summarizes them and writes
a deterministic index JSON.
