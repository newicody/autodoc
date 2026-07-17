# 0287-r7-r12 — Love memory, evidence and liaison synthesis

This patch closes the local chain after the two r11 specialist visits:

```text
two analyses
→ SQL authority and immutable context revisions
→ existing OpenVINO/E5 + Qdrant projection port
→ dense+sparse recall
→ SQL rehydration
→ local evidence mutualization
→ existing liaison synthesis
→ final local artifact envelope
```

The patch does not create a Scheduler, ControlProxy, OpenVINO runtime, Qdrant
client or GitHub publisher. It does not claim multi-laboratory validation: both
specialists currently execute in one concrete laboratory.

Apply from the repository root with:

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r12-love-memory-evidence-liaison-synthesis \
  --dry-run \
  --allow-dirty
```

Then use `--commit --push` after a green dry-run.
