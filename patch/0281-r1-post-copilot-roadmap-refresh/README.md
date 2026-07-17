# 0281-r1 — post-Copilot roadmap refresh

## Intention

Réaligner la documentation courante avec le jalon réellement atteint : le
workflow GitHub produit désormais la requête autoritative, l'avis Copilot et le
manifeste corrélé.

Le patch fixe ensuite la reprise opérationnelle :

```text
0281-r2 run-level assembly and existing 0275 intake
0281-r3 integration into the existing 0168 fetcher
0281-r4 pinned and cached Copilot CLI
0281-r5 advisory projection into the existing laboratory path
0281-r6 controlled idempotent Issue publication
0281-r7 real closed-loop smoke
```

## Portée

- modifie légèrement le README racine pour pointer vers la documentation
  courante détaillée ;
- ajoute `doc/README_CURRENT.md` ;
- ajoute changelog, manifeste, rapport et test de règle ;
- ne modifie aucun runtime.

## Application

```bash
python apply_patch_queue.py \
  --patch 0281-r1-post-copilot-roadmap-refresh \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0281-r1-post-copilot-roadmap-refresh \
  --commit \
  --push \
  --allow-dirty
```

## Test ciblé

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_post_copilot_roadmap_refresh_0281_rule.py
```

## Limites

Phase documentaire : aucun Scheduler, laboratoire runtime, réseau, GitHub API,
SQL, Qdrant, OpenVINO ou dépendance externe n'est ajouté.
