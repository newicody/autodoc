# Code rule — 0287 r16-r24 — file locale d’intake autorisé

> **Supplantée pour la recherche GitHub par r16-r24-r1.** Ces règles restent
> l’évidence historique du patch appliqué. Elles ne doivent plus orienter le
> chemin canonique, qui utilise des classes typées et PostgreSQL.

1. Réutiliser `src/context/authorized_route_request_queue.py` et
   `scheduler.route_requests.jsonl` avant d’introduire une nouvelle file.
2. Exiger `repository`, `run_id` et `policy_decision_id` explicitement.
3. Valider la requête avec `SchedulerRouteRequest.from_mapping`.
4. N’accepter qu’un rapport valide contenant exactement un intake autorisé.
5. Rejouer sans dupliquer un `request_id` identique.
6. Refuser un même `request_id` associé à un contenu différent.
7. Ne jamais démarrer un Scheduler tool-bounded pour franchir une frontière de
   processus vers le serveur local.
8. Ne pas appeler le Dispatcher, un handler, EventBus, ControlProxy, SQL, Qdrant
   ou un laboratoire dans l’écrivain de file.
9. Conserver le Dispatcher du noyau comme détail mécanique interne tant que
   `Scheduler.run()` en dépend ; ne pas lui attribuer d’autorité applicative.
10. Reporter la consommation de la file à une unité serveur séparée, possédée par
    le Scheduler canonique.
