# Phase 5.3-r1 — E5 artifact CLI import hygiene

## Objectif

Corriger l'hygiène d'import de la bordure CLI `context.e5_artifact_cli`.

La Phase 5.3 avait ajouté une CLI exécutable avec :

```bash
PYTHONPATH=src python -m context.e5_artifact_cli /tmp/autodoc_e5_dry_run
```

mais `src/context/__init__.py` réexportait aussi cette CLI. Cela provoquait un avertissement `runpy` quand le module était exécuté avec `python -m` :

```text
RuntimeWarning: 'context.e5_artifact_cli' found in sys.modules after import of package 'context', but prior to execution of 'context.e5_artifact_cli'
```

## Changement

- `src/context/__init__.py` ne réexporte plus la bordure CLI `e5_artifact_cli`.
- `python -m context.e5_artifact_cli` reste le point d'entrée explicite.
- Les contrats de domaine et de loader restent exportés par `context`.
- Un test verrouille cette frontière.

## Architecture

La CLI reste une bordure exécutable. Elle n'est pas une API automatique du package `context`.

```text
context package
  -> contrats runtime / loader / bridge

context.e5_artifact_cli
  -> bordure CLI explicite uniquement
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.3-r1 corrige une fuite de bordure CLI dans le package context ; aucune règle de programmation nouvelle n'est nécessaire.
```
