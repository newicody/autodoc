# Changelog — 0292 — Current architecture and Copilot routing context

## Ajouté
- Vue globale consolidée alignée sur le HEAD Git 56dc340 et l'intégration 0288.
- Spécification documentaire du snapshot serveur `missipy.server.routing_context_snapshot.v1`.
- Distinction explicite entre ProjectV2 #2 (source query-only) et ProjectV2 #3 (cible de recherche/projection).
- Séparation des observations matérielles 0288 et de la capacité/charge logique du Scheduler.

## Mis à jour
- `doc/README_CURRENT.md` : base du patch corrigée et statut 0292 ajouté.
- `doc/DOCUMENTATION_INDEX.md` : nouvelles références canoniques.

## Non modifié
- Aucun code runtime, Scheduler, handler, EventBus, ControlProxy ou backend.
- Aucun collecteur matériel, polling, service OpenRC, worker, queue, registre ou orchestrateur.
- Aucune dépendance externe.
- Aucune mutation GitHub / ProjectV2.

## Validation
- Tests non exécutés pour cette unité documentaire.
- Les validations historiques 0288 et r16-r66-r1 restent attachées à leurs propres rapports et commits.
