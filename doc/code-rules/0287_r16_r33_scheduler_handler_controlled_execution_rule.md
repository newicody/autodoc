# Règle r16-r33 — exécution contrôlée des handlers

1. Exécuter uniquement un `SchedulerHandlerExecutionLease` déjà armé.
2. Appeler exactement une fois `handler.execute()` par tentative non annulée et non expirée.
3. Borner l'appel par la deadline de tentative et un signal d'annulation injecté.
4. Convertir toute fin en objets typés `SchedulerTaskResult`, `SchedulerTaskFailure` ou `SchedulerTaskAttemptInterruption`.
5. Ne jamais laisser le handler décider du retry; injecter la classification de politique.
6. Exiger une projection explicite du résultat métier vers `result_type_ref` et `evidence_refs`.
7. Publier au mieux `SUCCEEDED`, `FAILED` ou `CANCELLED`, puis toujours `CLOSED`.
8. Toujours tenter la fermeture; une erreur de fermeture ne réécrit pas le résultat métier.
9. Une panne du canal informatif reste observation-only.
10. Ne persister aucune fin, ne libérer aucune ressource durable et ne choisir aucune tâche suivante dans cette unité.
11. Ne créer aucun Scheduler, Dispatcher, EventBus, laboratoire, file JSON ou JSONL.
12. VisPy reste observation-only et pourra conserver ou agréger les traces d'objets temporaires.
