# CHANGELOG — Phase 3.11 — E5 rank CLI

## Objectif

Exposer le mini-ranker local E5 depuis une commande de développement afin de tester une requête contre plusieurs passages avant l'introduction de Qdrant.

## Ajouts

- `src/inference/e5_rank_cli.py`
  - parser CLI `missipy-rank-e5` ;
  - sortie texte lisible ;
  - sortie JSON stable ;
  - lecture de passages via `--passage` répété ;
  - lecture de passages depuis `--passages-file` ;
  - limite de résultats via `--limit`.
- `tools/rank_e5.py`
  - lanceur local depuis la racine du dépôt.
- `tests/inference/test_e5_rank_cli.py`
  - tests portables avec pipeline fake ;
  - aucun OpenVINO requis ;
  - aucun modèle local requis.

## Modifications

- `src/inference/__init__.py`
  - export des entrées CLI de ranking.
- `README.md`
  - documentation de la commande `tools/rank_e5.py`.
- `doc/ARCHITECTURE_LAYERS.md`
  - ajout de la couche CLI de ranking local.

## Contraintes respectées

- Aucun changement Scheduler.
- Aucun import OpenVINO supplémentaire.
- Aucun Qdrant.
- Aucun `.svg` généré.
- Aucun script de patch.

## Validation

```text
compileall OK
153 passed, 1 skipped
main.py exit code: 0
DOT_OK
```
