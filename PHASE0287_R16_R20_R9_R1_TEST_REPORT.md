# Rapport de test — 0287 r16-r20-r9-r1

## Unité

`cabler-adaptateur-repository-owner-sans-modifier-publisher`

## Portée

- héritage de l’adaptateur GitHub existant;
- résolution `repositoryOwner`;
- normalisation vers le contrat pur historique;
- support User et Organization;
- câblage dans `prepare` et `complete`;
- aucune modification du publisher exécutable;
- absence d’un second transport ou d’une seconde mutation.

## Vérifications du bundle

- syntaxe AST : réussie;
- `git apply --check` contre les fichiers r4 actuels : réussi;
- `git diff --check` : réussi;
- publisher historique absent du diff : confirmé;
- README cumulatif non modifié;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
