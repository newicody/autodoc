# Raccord PostgreSQL du lancement Scheduler — 0287 r16-r31-r1-r1

Cette unité raccorde `DbApiSchedulerTaskLaunchTransaction` au binding PostgreSQL local déjà propriétaire de la connexion. La même connexion DB-API alimente :

```text
autorité des révisions de contexte
+ store relationnel des commandes Scheduler
+ transaction relationnelle des lancements de tâches
```

Le schéma du lancement est initialisé pendant le bootstrap PostgreSQL existant.
Le binding expose ensuite la transaction comme port typé. Aucune connexion supplémentaire, aucun pilote supplémentaire et aucun runtime parallèle ne sont créés.

La fermeture reste possédée par `LovePostgreSqlAuthorityBinding` : fermer
l’autorité de contexte ferme exactement une fois la connexion partagée. Les
stores et la transaction de lancement ne possèdent pas une fermeture séparée.

Cette unité ne démarre pas le Scheduler, n’instancie aucun handler et ne produit
aucune notice `CREATED` ou `STARTED`. PostgreSQL reste l’autorité durable. Il
n’existe aucune colonne JSON d’autorité et aucune file JSONL. Le Dispatcher n’est pas appelé. EventBus, PassiveSupervisor et VisPy restent observation-only.

Le raccord au processus serveur et au Scheduler canonique déjà actif demeure l’unité suivante. Le runtime `tool-bounded` historique n’est pas étendu par ce patch.
