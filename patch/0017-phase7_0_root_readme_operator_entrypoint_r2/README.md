# 0017 r2 — Phase 7.0 Root README Operator Entrypoint

This patch rewrites the root README as a stable operator/developer entrypoint before Part 7 external projection work.

This r2 archive fixes the README patch context so `git apply --check` applies against the current 3-line root README.

## Apply

```bash
python apply_patch_queue.py --patch 0017-phase7_0_root_readme_operator_entrypoint_r2 --dry-run
python apply_patch_queue.py --patch 0017-phase7_0_root_readme_operator_entrypoint_r2 --commit --push
```

## Scope

- Rewrite `/README.md`.
- Document local-first source of truth.
- Document patch queue workflow.
- Document current SourceCandidate chain.
- Add AI-assisted development and hardware accessibility context.
- Add README guard tests.
- Add release docs, changelog, manifest and test report.

## Out of scope

- No runtime code.
- No external API.
- No network.
- No GitHub mutation.
- No Scheduler change.
