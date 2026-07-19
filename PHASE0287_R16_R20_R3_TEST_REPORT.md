# Rapport de test — 0287 r16-r20-r3

## Unité

`resoudre-cible-projectv2-recherche-github`

## Portée

- résolution exacte ProjectV2/Issue/champ;
- réutilisation du contrat de domaine existant;
- réutilisation de l’adaptateur GitHub CLI existant;
- sortie JSON, résumé et variables shell;
- overrides couplés;
- aucune mutation distante.

## Vérifications du bundle

- syntaxe AST : réussie;
- frontières statiques : réussies;
- `git apply --check` contre le README courant : réussi;
- `git diff --check` : réussi;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
