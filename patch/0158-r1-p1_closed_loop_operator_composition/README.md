# 0158-r1 — P1 closed-loop operator composition

Corrected replacement for the previous broken 0158 patch.

Apply:

```bash
tar -xzf autodoc_patch_0158-r1-p1_closed_loop_operator_composition.tar.gz
python apply_patch_queue.py --patch 0158-r1-p1_closed_loop_operator_composition --dry-run --allow-dirty
python apply_patch_queue.py --patch 0158-r1-p1_closed_loop_operator_composition --commit --push --allow-dirty
```

The old untracked `patch/0158-p1_closed_loop_operator_composition/` directory can
be removed or ignored.
