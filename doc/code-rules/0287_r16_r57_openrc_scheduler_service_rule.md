# Règle 0287 r16 r57 — service OpenRC du Scheduler canonique

1. OpenRC possède uniquement le processus, le PID, le démarrage, l'arrêt et le
   redémarrage.
2. Le service réutilise exactement un Scheduler canonique injecté et ne crée
   aucun second Scheduler, Dispatcher ou EventBus.
3. La boucle appelle uniquement le runtime `externally-managed` déjà composé,
   avec une borne explicite de tâches par tick.
4. PostgreSQL reste l'autorité durable. Aucun stockage interne JSON et aucune
   file JSONL ne servent de queue, de graphe ou d'état canonique.
5. ControlFS et `/dev/shm` restent un plan rapide ; Qdrant reste projection et
   rappel.
6. La fabrique de backends est explicite sous forme `module:function`. Aucun
   backend réel n'est chargé implicitement par le noyau.
7. SIGTERM et SIGINT demandent un arrêt coopératif. Le service appelle
   `Scheduler.shutdown()` puis rejoint la tâche `Scheduler.run()` avant la
   fermeture des backends.
8. Les secrets restent dans un fichier d'environnement local non versionné.
9. VisPy, PassiveSupervisor et EventBus restent observation-only.

code_rule_review: done
code_rule_update_required: true
code_rule_reason: nouvelle frontière de propriété de processus OpenRC, sans modification du noyau Scheduler.
