# Rapport de test — 0287 r16-r22

## Unité

`verrouiller-workflow-automatique-issue-opened`

## Portée

- suppression du bloc `workflow_dispatch`;
- suppression des quatre inputs;
- suppression des fallbacks `inputs.*`;
- source unique `github.event.issue`;
- intention initiale constante;
- Copilot requis sans variable d’activation;
- conservation du filtre de forme de l’Issue;
- conservation des trois uploads existants.

## Vérifications du bundle

- parsing YAML avec `BaseLoader` : réussi;
- déclencheur exact `issues/opened` : confirmé;
- `workflow_dispatch` absent comme trigger : confirmé;
- `inputs.` absent : confirmé;
- syntaxe AST du test : réussie;
- `git apply --check` contre le workflow master audité : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
