# 0030 — Phase 7.13 Documentation SVG Build Policy

This patch adds a documentation SVG build policy tool.

The current policy is:

```text
doc/docs/architecture/context/*.svg -> source-only generated files, remove after make
other doc/docs/architecture/**/*.svg -> publishable generated files, keep
```

## Apply

```bash
python apply_patch_queue.py --patch 0030-phase7_13_documentation_svg_build_policy --dry-run
python apply_patch_queue.py --patch 0030-phase7_13_documentation_svg_build_policy --commit --push
```

## After this patch, safe make workflow

```bash
cd doc
make
cd ..

python tools/docs_svg_build_policy.py   --root .   --clean   --check   --report-file doc/maintenance/docs_svg_build_policy_report.json

PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Scope

- Add SVG build policy tool.
- Make global documentation build usable with a post-build cleanup/check.
- Preserve source-only rules for context diagrams.
- Do not modify the makefile yet.

## Out of scope

- No makefile rewrite.
- No network.
- No Scheduler change.
- No SVG versioning policy change.
