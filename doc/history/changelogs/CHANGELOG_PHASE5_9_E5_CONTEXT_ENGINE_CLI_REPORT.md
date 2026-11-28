# Changelog — Phase 5.9 — E5 ContextEngine CLI report file

## Résumé

La Phase 5.9 ajoute une persistance optionnelle du payload de la CLI manuelle `context.e5_context_engine_cli`.

Elle ne crée pas de nouvelle commande : elle ajoute seulement :

```text
--report-file FILE
```

à la bordure CLI de la Phase 5.8.

## Flux

```text
artifact-dir Phase 4
-> ContextEngine.attach_e5_artifact_dir()
-> E5ContextEngineStatus
-> payload missipy.e5.context_engine_cli.v1
-> stdout text/json
-> report JSON atomique optionnel
```

## Fichiers modifiés

- `src/context/e5_context_engine_cli.py`
  - ajoute `E5ContextEngineCliReportPolicy` ;
  - ajoute `--report-file` ;
  - écrit le payload CLI JSON de manière atomique ;
  - conserve les erreurs IO dans la bordure CLI.

- `tests/context/test_e5_context_engine_cli.py`
  - vérifie l'écriture de rapport ;
  - vérifie l'erreur si la cible `--report-file` est un répertoire.

- `doc/docs/architecture/context/32_e5_context_engine_cli.dot`
  - ajoute la navigation vers 5.9.

- `doc/docs/architecture/context/33_e5_context_engine_cli_report.dot`
  - décrit la nouvelle persistance optionnelle.

- `doc/docs/architecture/00_global.dot`
  - rend la Phase 5.9 visible dans la carte globale.

## Frontières

La Phase 5.9 ne déclenche aucun Scheduler vivant, daemon, backend, réseau, GitHub API, Qdrant, LLM ou appel OpenVINO.

L'écriture fichier reste un effet de bord de CLI.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.9 ajoute une écriture optionnelle dans une bordure CLI existante ; aucune règle de programmation nouvelle n'est nécessaire.
```
