# 0286-r4-r1 — Correctif cumulatif des règles ProjectV2

Ce correctif s'applique après que le patch `0286-r4` a été appliqué dans
l'arbre de travail et que la suite `tests/rules` a échoué sur les deux règles
historiques signalées.

Il ne réapplique pas r4 et ne modifie ni `projectv2_views.json` ni
`INSTALLATION.md`.

## Application

```bash
python apply_patch_queue.py \
  --patch 0286-r4-r1-specialist-capability-growth-projectv2-cumulative-rule-fix \
  --commit \
  --push \
  --allow-dirty
```

## Portée

- rend la règle 0284 compatible avec des vues additives ;
- rend la règle d'audit 0286-r1 compatible avec la fermeture atomique du gap r4 ;
- conserve le rejet d'une installation partielle des neuf champs ;
- ajoute rapport, architecture, graphe, changelog, manifeste et règle de
  non-régression ;
- vérifie le guide cumulatif `newicody/projects` sans le modifier.
