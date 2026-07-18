# Rapport 0287 r16-r4-r3-r4

## Objet

Créer automatiquement un triplet d'artefacts pour chaque nouvelle Issue de
recherche du dépôt dédié `newicody/projects`.

## Contrats vérifiés

- événement `issues.opened` ;
- dépôt exact `newicody/projects` ;
- formulaire identifié par `[Recherche] ` ou ses deux sections obligatoires ;
- résolution automatique `Recherche` / `initial` ;
- avis Copilot requis pour le run automatique ;
- trois uploads corrélés par l'identité lisible existante ;
- conservation du `workflow_dispatch` pour les opérations manuelles ;
- aucune utilisation des vues ProjectV2 comme condition synchrone du webhook.

## Commandes

```bash
/home/eric/python/bin/python -m compileall -q src tools tests
/home/eric/python/bin/python -m pytest -q \
  tests/rules/test_projects_new_research_issue_artifacts_0287_rule.py \
  tests/rules/test_projects_owned_copilot_issue_comment_token_0287_rule.py
/home/eric/python/bin/python -m pytest -q tests/rules
```

## Résultat local du bundle

```text
5 tests ciblés réussis
YAML workflow et formulaire chargés avec PyYAML BaseLoader
git diff --check réussi
```
