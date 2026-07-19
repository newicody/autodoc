# Rapport de test — 0287 r16-r21

## Unité

`demarrer-cycle-recherche-github-propre`

## Portée

- plan digesté sans accès distant;
- forme d’Issue déclenchable;
- trois gates de mutation;
- création d’une Issue unique;
- ajout au ProjectV2;
- exclusion des runs préexistants;
- découverte d’un unique run `issues`;
- attente d’une conclusion `success`;
- vérification d’un artefact par rôle;
- refus des runs et rôles dupliqués;
- absence de `workflow_dispatch`;
- arrêt avant le fetch local.

## Vérifications du bundle

- syntaxe AST : réussie;
- frontières statiques : réussies;
- `git apply --check` sur arbre propre : réussi;
- `git diff --check` : réussi;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
