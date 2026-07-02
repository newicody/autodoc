# Documentation SVG build policy

The repository keeps architecture DOT sources under:

```text
doc/docs/architecture
```

Some diagrams are publishable as generated SVG, but the `context` architecture
diagrams are source-only. If a global documentation build generates SVG files
under `doc/docs/architecture/context`, they must be removed before rule tests
run.

## Current workflow

```bash
cd doc
make
cd ..

python tools/docs_svg_build_policy.py \
  --root . \
  --clean \
  --check \
  --report-file doc/maintenance/docs_svg_build_policy_report.json

PYTHONPATH=src:. pytest -q tests/rules
```

This makes `make` usable again while preserving the source-only rule for context
diagrams.

## Dry-run

```bash
python tools/docs_svg_build_policy.py \
  --root . \
  --report-file doc/maintenance/docs_svg_build_policy_report.json
```

## Clean and check

```bash
python tools/docs_svg_build_policy.py \
  --root . \
  --clean \
  --check \
  --report-file doc/maintenance/docs_svg_build_policy_report.json
```
