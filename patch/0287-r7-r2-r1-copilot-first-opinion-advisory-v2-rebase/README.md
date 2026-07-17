# 0287-r7-r2-r1-copilot-first-opinion-advisory-v2-rebase

## Objet

Correction de rebase du patch `0287-r7-r2`. Le premier bundle remplaçait le
bloc de prompt avec un contexte trop large et ne pouvait pas s'appliquer sur le
runner déjà enrichi dans le checkout réel.

Cette révision :

- conserve le câblage existant du runner ;
- ajoute un constructeur actif de prompt v2 à un point d'insertion stable ;
- transmet `title`, `body`, `labels` et, lorsqu'ils existent,
  `autodoc_dispatch` et `context` ;
- produit `missipy.github.copilot_advisory.v2` avec uniquement les quatre champs
  analytiques demandés ;
- garde la lecture historique v1 pendant la migration ;
- ne modifie ni Scheduler, ni laboratoire, ni SQL, ni Qdrant, ni publication
  distante.

Ne pas appliquer l'archive précédente
`0287-r7-r2-copilot-first-opinion-advisory-v2`.

## Application

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-r1-copilot-first-opinion-advisory-v2-rebase \
  --dry-run \
  --allow-dirty
```

Puis, après un dry-run vert :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r2-r1-copilot-first-opinion-advisory-v2-rebase \
  --commit \
  --push \
  --allow-dirty
```

## Tests ciblés

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_copilot_first_opinion_advisory_v2_0287_r7_r2.py \
  tests/rules/test_copilot_first_opinion_advisory_v2_0287_r7_r2_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
```
