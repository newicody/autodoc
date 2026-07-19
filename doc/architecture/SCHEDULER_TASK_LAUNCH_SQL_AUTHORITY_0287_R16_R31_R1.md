# Autorité SQL transactionnelle des lancements — 0287 r16-r31-r1

Cette unité implémente le port `SchedulerTaskLaunchTransaction` avec la connexion DB-API déjà possédée par le binding PostgreSQL local. Elle n’ouvre aucun pilote
et refuse une connexion en `autocommit`.

La transaction atomique vérifie puis enregistre ensemble :

```text
commande déjà claimed par le Scheduler canonique
+ version de tâche ready
+ consommation du budget de commande
+ disponibilité réelle des ressources
+ réservation durable
+ tâche running
+ tentative running
+ transition ready → running
+ reçu transactionnel immuable
```

Une divergence de version, une ressource devenue indisponible ou un propriétaire
de claim différent provoque un rollback complet. Un rejeu strictement identique
retourne le même reçu sans nouvelle consommation de budget ou de ressource.

PostgreSQL reste l’autorité durable. Le stockage est relationnel et normalisé :
aucune colonne JSON, aucune file JSONL et aucun fichier interne ne porte
l’autorité. Le Scheduler reste l’autorité d’orchestration ; aucun handler n’est
instancié ou exécuté. Le Dispatcher n’est pas appelé. EventBus,
PassiveSupervisor et VisPy restent observation-only.

L’inventaire SQL de ressources est une photographie autoritative utilisée pour
la comparaison transactionnelle. Le helper d’amorçage ne constitue ni un
ResourceManager ni une nouvelle boucle d’orchestration.
