# Rapport de test — 0287 r16-r22-r1

## Unité

`migrer-regles-historiques-cycle-automatique`

## Cause

r16-r22 a correctement retiré `workflow_dispatch` et rendu Copilot
obligatoire sur le chemin automatique `issues: opened`. Cinq règles
historiques continuaient toutefois à imposer le contrat précédent.

## Migration

- le template générique dual-artifact reste Copilot optionnel;
- le workflow Projects automatique exige Copilot;
- `workflow_dispatch` et `inputs.*` sont interdits sur ce workflow;
- l’intention initiale est vérifiée par ses constantes directes;
- les permissions read-only et les trois uploads restent exigés.

## Frontières

- aucun fichier de workflow modifié;
- aucun code runtime modifié;
- aucune permission GitHub modifiée;
- aucune documentation d’installation réécrite;
- uniquement quatre fichiers de règles historiques et ce rapport.

## Vérifications du bundle

- syntaxe AST des quatre règles : réussie;
- `git apply --check` sur les baselines auditées : réussi;
- `git diff --check` : réussi;
- aucun cache Python inclus.

La suite complète est exécutée par `apply_patch_queue.py`.
