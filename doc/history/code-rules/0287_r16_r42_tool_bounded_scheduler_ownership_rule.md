# Règle 0287 r16 r42 — propriété du Scheduler `tool-bounded`

Pour un runtime déclaré `tool-bounded`, l'adaptateur de préparation peut lancer
une tâche asyncio portant **le même Scheduler injecté** uniquement lorsque ce
Scheduler est arrêté. Il doit vérifier l'état actif avant le dispatch, puis
arrêter et rejoindre cette tâche exacte dans un `finally` avant que l'outil ne
ferme les ressources de la lease.

Il est interdit de créer un Scheduler, Dispatcher, EventBus, registre ou file
supplémentaire. Il est également interdit de déplacer ce cycle dans un thread,
un processus, un daemon ou un orchestrateur parallèle. Il ne doit exister
aucun second Scheduler.

Un Scheduler déjà actif n'est pas relancé. Un Scheduler `externally-managed`
n'est jamais arrêté par l'adaptateur et doit être actif avant toute opération.

Le dispatch métier conserve son contrôle fail-closed : il consomme uniquement
un Scheduler déjà actif et ne devient jamais propriétaire de son cycle de vie.
