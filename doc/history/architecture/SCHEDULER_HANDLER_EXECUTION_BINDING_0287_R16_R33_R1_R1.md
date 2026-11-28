# Raccord PostgreSQL de fin d’exécution — 0287 r16-r33-r1-r1

Cette unité raccorde `DbApiSchedulerHandlerExecutionTransaction` au binding
PostgreSQL local déjà propriétaire de la connexion. La même connexion DB-API
alimente l’autorité des révisions de contexte, le store des commandes, la
transaction de lancement et la transaction de fin d’exécution.

Le schéma de fin d’exécution est initialisé pendant le bootstrap PostgreSQL
existant. Le binding expose ensuite la transaction comme port typé. Aucune
connexion, aucun pilote, aucun pool et aucun runtime supplémentaire ne sont
créés.

La fermeture reste possédée par `LovePostgreSqlAuthorityBinding` : fermer
l’autorité de contexte ferme exactement une fois la connexion partagée. Les
transactions de lancement et de fin ne possèdent pas de fermeture séparée.

Cette unité ne rejoue pas le handler, ne recalcule pas le graphe, ne promeut
aucune tâche et ne décide pas d’un retry. PostgreSQL reste l’autorité durable.
Aucune autorité n’est stockée en JSON ou JSONL. Dispatcher n’est pas appelé.
EventBus, PassiveSupervisor et VisPy restent observation-only.

La relecture de l’état durable et la décision Scheduler suivante appartiennent
à l’unité r16-r34.
