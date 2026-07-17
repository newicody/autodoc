# 0287-r7-r15-r2-r4-readable-copilot-publication-wiring

Apply after `0287-r7-r15-r2-r3-r1-human-readable-artifact-workflow-compatibility-fix`.

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r4-readable-copilot-publication-wiring \
  --dry-run \
  --allow-dirty
```

Then:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r2-r4-readable-copilot-publication-wiring \
  --commit \
  --push \
  --allow-dirty
```

The tool is preview-first. It reuses the existing Issue and ProjectV2 mutation adapters and requires all three remote gates plus one exact combined digest for execution.
