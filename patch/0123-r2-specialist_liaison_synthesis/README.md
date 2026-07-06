# 0123-r2 — Specialist Liaison Synthesis

This patch replaces the rejected 0123 GitHub publication review direction.

It adds a local specialist liaison/synthesis boundary:

```text
specialist outputs
-> SpecialistOutputFragment[]
-> SpecialistPathTrace bus-ready observations
-> SpecialistLiaisonSynthesis
-> optional FinalSynthesisPacket only after liaison
```

No GitHub client, no DOT publication review, no watcher/service, no live bus subscription, and no kernel/runtime authority changes are added.

## Apply

```bash
python apply_patch_queue.py --patch 0123-r2-specialist_liaison_synthesis --dry-run
python apply_patch_queue.py --patch 0123-r2-specialist_liaison_synthesis --commit --push
```

If the rejected `0123-github_publication_review` patch was already partially applied, do not apply this on top blindly; first inspect/remove that wrong patch state or ask for a corrective revert patch.
