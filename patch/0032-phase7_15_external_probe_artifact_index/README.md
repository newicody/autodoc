# 0032 — Phase 7.15 External Probe Artifact Index

This patch adds a local artifact index for SourceCandidate external probe bundles.

## Apply

```bash
python apply_patch_queue.py --patch 0032-phase7_15_external_probe_artifact_index --dry-run
python apply_patch_queue.py --patch 0032-phase7_15_external_probe_artifact_index --commit --push
```

## Scope

- Add local external probe artifact index module.
- Add CLI for indexing local probe bundles.
- Scan local manifest.json files only.
- Add tests, rules and documentation.

## Out of scope

- No external calls.
- No network.
- No remote mutation.
- No Scheduler change.
- No DOT.
- No SVG.
