# Changelog — Phase 4.13 E5 unified command surface

## Ajout

- Nouveau module `src/inference/e5_tool_cli.py`.
- Nouveau script `tools/e5.py`.
- Nouvelle intention typée `E5ToolCommand`.
- Nouvelle politique de routage `E5ToolDispatchPolicy`.
- Tests `tests/inference/test_e5_tool_cli.py`.

## Comportement

La façade unique accepte :

```text
embed
rank
build
search
rebuild
inspect
```

Chaque sous-commande délègue à l'adaptateur existant, sans dupliquer la logique métier.

## Compatibilité

Les scripts historiques restent valides et ne sont pas supprimés.

## Hors périmètre

- Pas de Qdrant.
- Pas de Scheduler.
- Pas de changement `missipy.e5.corpus.v1`.
- Pas de suppression des wrappers historiques.
- Pas de nouveau backend.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: la règle de réduction de surface CLI était déjà définie en Phase 4.12-r2 ; cette phase l'applique sans modifier la guideline.
```
