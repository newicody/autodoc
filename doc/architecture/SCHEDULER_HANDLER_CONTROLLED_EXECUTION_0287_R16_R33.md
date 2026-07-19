# Exécution contrôlée des handlers Scheduler — 0287 r16-r33

Cette unité consomme un `SchedulerHandlerExecutionLease` déjà armé et appelle
exactement une fois `handler.execute()` sous l'autorité du Scheduler canonique.
Elle ne crée ni Scheduler, ni Dispatcher autonome, ni laboratoire parallèle.

```text
lease STARTED
→ contrôle de deadline et du signal d'annulation
→ un seul appel asynchrone à handler.execute()
→ résultat ou erreur typée
→ transition de tâche gouvernée par SchedulerTask
→ notice SUCCEEDED / FAILED / CANCELLED
→ fermeture toujours tentée
→ notice CLOSED
→ SchedulerHandlerExecutionOutcome
→ arrêt avant persistance SQL de fin
```

Les issues prises en charge sont `succeeded`, `failed`, `retry-wait`,
`cancelled` et `timed-out`. La décision de reprise ne vient jamais du handler :
elle est fournie par un classificateur de politique injecté, puis bornée par le
budget de tentatives déjà porté par `SchedulerTask`.

La projection du résultat métier est également injectée. Elle produit seulement
un `result_type_ref` et des références de preuve; le Scheduler conserve l'objet
résultat en mémoire jusqu'à la transaction durable suivante. PostgreSQL reste l'autorité durable et aucune file JSON ou JSONL n'est ajoutée.

La fermeture est explicitement injectée et toujours tentée. Une erreur de
fermeture est conservée dans `SchedulerHandlerCloseReceipt`, sans transformer
rétroactivement une réussite métier en échec. Le Scheduler décidera de la suite
après persistance de l'issue complète.

Les notices informatives sont observation-only. Un défaut du sink n'annule ni
la capacité, ni sa transition typée. PassiveSupervisor et VisPy pourront garder
une trace persistante ou agrégée des apparitions et disparitions des instances,
notamment `CREATED`, `STARTED`, la phase terminale et `CLOSED`; VisPy reste
observation-only et ne modifie jamais l'exécution.

Cette unité ne persiste pas l'issue, ne libère pas durablement les ressources,
ne choisit pas la tâche suivante et n'appelle ni EventBus, ni Qdrant, ni GitHub.
La transaction de fin appartient à r16-r33-r1.
