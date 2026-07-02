# Phase 5.4-r1 — E5 local context runtime test fix

## Résumé

Correction ciblée du test `tests/context/test_e5_local_context_runtime.py`.

Le fixture pytest `tmp_path` fournit déjà un dossier existant. Le helper de test `_write_artifacts()` tentait de créer ce dossier avec `directory.mkdir()` sans `exist_ok=True`, ce qui provoquait `FileExistsError` avant d'exercer le runtime.

La correction remplace l'appel par :

```python
directory.mkdir(parents=True, exist_ok=True)
```

## Portée

- Aucun changement runtime.
- Aucun changement de contrat.
- Aucun changement CLI.
- Aucun changement Scheduler.
- Aucun changement Qdrant.
- Aucun changement réseau.
- Aucun changement GitHub.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.4-r1 corrige uniquement un helper de test ; aucune règle de programmation nouvelle n'est nécessaire.
