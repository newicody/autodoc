# Phase 5.8 — E5 ContextEngine manual CLI intake

## Résumé

La Phase 5.8 ajoute une bordure CLI locale et manuelle autour du raccord 5.6/5.7 :

```text
artifact-dir Phase 4
-> ContextEngine.attach_e5_artifact_dir()
-> inspect_e5_context_engine()
-> text/json
```

Cette phase ne démarre aucun daemon, ne lance aucun Scheduler vivant, ne lit aucun réseau, n'appelle aucune API GitHub, ne branche pas Qdrant, ne génère aucune réponse LLM et n'appelle pas OpenVINO.

## Fichiers

- `src/context/e5_context_engine_cli.py`
- `tests/context/test_e5_context_engine_cli.py`
- `doc/docs/architecture/context/32_e5_context_engine_cli.dot`
- `doc/docs/architecture/context/31_e5_context_engine_status.dot`
- `doc/docs/architecture/00_global.dot`

## Commande

```bash
PYTHONPATH=src python3 -m context.e5_context_engine_cli /tmp/autodoc_e5_dry_run
PYTHONPATH=src python3 -m context.e5_context_engine_cli --format json /tmp/autodoc_e5_dry_run
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.8 ajoute une bordure CLI manuelle autour de contrats existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
