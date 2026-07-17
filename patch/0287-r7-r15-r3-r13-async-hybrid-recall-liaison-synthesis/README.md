# 0287-r7-r15-r3-r13-async-hybrid-recall-liaison-synthesis

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r13-async-hybrid-recall-liaison-synthesis \
  --dry-run \
  --allow-dirty
```

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r13-async-hybrid-recall-liaison-synthesis \
  --commit \
  --push \
  --allow-dirty
```

This unit consumes the already-completed r12 live binding. It does not project
analyses again. Full functional validation runs in the repository Patch Queue.
