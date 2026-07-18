# Rapport de test — 0287 r16-r9

## Unité

`remettre-demande-recherche-au-scheduler-existant`

## Portée

- nouveau type d’événement `SCHEDULER_ROUTE_REQUEST`;
- réutilisation de `ImportedActionsRuntimePorts`;
- enregistrement idempotent du handler ControlProxy existant;
- émission par `scheduler.emit()`;
- attente de la réponse coopérative via `Request.reply`;
- validation du readback de route;
- aucune exécution laboratoire ou spécialiste.

## Vérifications du bundle

- compilation Python des fichiers ajoutés : réussie;
- smoke isolé avec Scheduler/Dispatcher simulés : réussi;
- insertion du type d’événement vérifiée sur une copie de `event.py`;
- `git diff --check` : réussi;
- `git apply --check` sur la base synthétique : réussi.

La suite complète `tests/rules` est exécutée par `apply_patch_queue.py` dans le
checkout utilisateur.
