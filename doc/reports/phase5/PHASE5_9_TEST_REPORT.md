# Phase 5.9 — Test report

## Scope

Valider que la CLI manuelle `context.e5_context_engine_cli` peut persister son payload JSON complet dans un fichier optionnel sans créer une nouvelle commande.

## Tests recommandés côté dépôt utilisateur

```bash
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_cli.py
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_status.py
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_intake.py
PYTHONPATH=src pytest -q tests/context/test_context_engine.py::test_context_engine_uses_event_path_for_snapshot
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Pré-vérifications faites dans l'environnement de génération

```text
py_compile src/context/e5_context_engine_cli.py: OK
DOT 00_global.dot: OK
DOT 32_e5_context_engine_cli.dot: OK
DOT 33_e5_context_engine_cli_report.dot: OK
```

Le sandbox de génération ne contient pas tout l'historique de modules du dépôt utilisateur ; les tests pytest complets sont donc à relancer localement après extraction.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.9 ajoute une écriture optionnelle dans une bordure CLI existante ; aucune règle de programmation nouvelle n'est nécessaire.
```
