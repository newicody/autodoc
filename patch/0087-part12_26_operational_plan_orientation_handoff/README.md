# 0087-part12_26_operational_plan_orientation_handoff

Phase 0087 : docs de plan opérationnel, orientation et handoff nouvelle conversation.

## Ajouts

```text
doc/architecture/OPERATIONAL_RUNTIME_PLAN_0087.md
doc/architecture/NEW_CONTEXT_HANDOFF_0087.md
doc/changelog/0087-operational-plan-orientation-handoff.md
tests/rules/test_operational_plan_orientation_handoff_rule.py
```

## Modifie

```text
doc/architecture/REAL_IMPLEMENTATION_SEQUENCE_0081.md
```

## Application

```bash
cd ~/projet/git/autodoc
PATCH_ID=0087-part12_26_operational_plan_orientation_handoff
unzip -o /chemin/vers/${PATCH_ID}.zip -d .
python apply_patch_queue.py --patch $PATCH_ID --dry-run
python apply_patch_queue.py --patch $PATCH_ID --commit --push
```

## Gate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules
```

## Prochaine phase

0088 : handler Scheduler concret qui appelle `handle_scheduler_route_request()` sans modifier le loop.
