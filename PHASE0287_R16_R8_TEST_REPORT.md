# Rapport de test — 0287 r16-r8

## Unité

`transformer-recherche-admissible-en-demande-scheduler-autorisee`

## Portée

- politique automatique explicite limitée à `newicody/projects`;
- décision `approve` déterministe après admissibilité r16-r6;
- réutilisation de `build_github_artifact_scheduler_intake_plan`;
- production d’un `SchedulerRouteRequest` autorisé;
- aucun dispatch Scheduler;
- aucune exécution laboratoire;
- aucune écriture SQL/Qdrant et aucune mutation GitHub.

## Vérifications du bundle

- compilation Python des nouveaux fichiers : réussie;
- smoke isolé avec le contrat d’intake simulé : réussi;
- `git diff --check` : réussi;
- `git apply --check` sur une base vide : réussi.

La suite complète est exécutée par `apply_patch_queue.py` dans le checkout
utilisateur.
