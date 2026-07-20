# Propriété du cycle Scheduler `tool-bounded` — 0287 r16 r42

## Problème observé

Le runtime installé composait un Scheduler canonique process-local, mais le
retournait arrêté. Le dispatch de recherche refusait correctement de démarrer
un second Scheduler et exigeait une autorité déjà active. Le chemin opérationnel
s'arrêtait donc avant l'exécution des spécialistes.

## Frontière retenue

L'adaptateur de préparation `tool-bounded` enveloppe la composition existante.
Il démarre uniquement le Scheduler déjà injecté dans les ports, dans la même
boucle asyncio et dans le même processus. Il attend son état actif, exécute la
composition existante, demande ensuite son arrêt et rejoint la tâche exacte
qu'il a créée avant que l'outil ferme PostgreSQL et Qdrant.

Le résultat préparé reste transparent pour l'outil existant. Sa méthode
`to_mapping()` ajoute une preuve sérialisable `scheduler_cycle`, sans exposer
l'objet Scheduler ni sa tâche asyncio.

```text
outil opérationnel inchangé
    -> adaptateur de préparation
    -> même Scheduler injecté
    -> create_task(scheduler.run())
    -> running == true
    -> composition prepare existante
    -> scheduler.shutdown()
    -> attente de la même tâche
    -> résultat préparé + scheduler_cycle
    -> fermeture de la lease par l'outil
```

## Cas de propriété

- `tool-bounded` et Scheduler arrêté : l'adaptateur possède ce cycle, le démarre
  et l'arrête exactement une fois.
- `tool-bounded` et Scheduler déjà actif : réutilisation sans relance ni arrêt.
- `externally-managed` et Scheduler actif : réutilisation sans prise de
  propriété.
- `externally-managed` et Scheduler arrêté : échec fermé explicite.
- exception dans la composition : arrêt du cycle `tool-bounded` dans le
  `finally`, puis fermeture normale de la lease par l'outil existant.

## Invariants

Cette unité ne crée aucun Scheduler, Dispatcher, EventBus, registre, file,
thread, processus, daemon ou stockage durable parallèle. Le contrôle fail-closed
de `github_research_scheduler_dispatch_0287` reste inchangé. PostgreSQL demeure
l'autorité durable et le Scheduler demeure l'unique autorité d'orchestration.
