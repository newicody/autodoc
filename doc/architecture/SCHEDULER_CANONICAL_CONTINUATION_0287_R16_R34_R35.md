# Continuation durable et cycle borné du Scheduler — 0287 r16-r34/r16-r35

Cette unité regroupe deux étapes du chemin critique :

1. relire PostgreSQL après le commit terminal d’un handler, reconstruire le
   graphe typé et promouvoir durablement les dépendances devenues `ready` ;
2. exécuter un tick borné du Scheduler canonique déjà actif.

Le cycle ne crée aucun Scheduler, aucun Dispatcher autonome, aucun daemon et
aucune file JSON ou JSONL. PostgreSQL reste l’autorité durable. Le port
`SchedulerReadyTaskStepRunner` réutilise la chaîne déjà développée : admission,
transaction de lancement, création du handler, exécution contrôlée et
transaction de fin.

Chaque tick est limité par `max_task_steps`. Après chaque issue de handler, le
cycle relit PostgreSQL avant toute nouvelle décision. Il refuse de continuer si
la tâche exécutée est encore `ready` après la relecture durable.

Le Scheduler reste l’unique autorité pour choisir la prochaine tâche. Les
handlers ne créent pas leurs successeurs et le Dispatcher historique ne reçoit
aucune responsabilité applicative nouvelle.

L’EventBus, PassiveSupervisor et VisPy restent des surfaces d’observation.
VisPy reste observation-only ; sa future mémoire temporelle pourra conserver ou
agréger les apparitions et disparitions sans modifier la continuation.
