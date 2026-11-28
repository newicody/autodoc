# Règle r16-r33-r1

1. Persister l’issue du handler et libérer la réservation dans une transaction atomique.
2. Comparer le lancement, les versions de tâche et tentative, le Scheduler propriétaire et les digests.
3. Enregistrer séparément résultat, échec ou interruption dans des tables relationnelles.
4. Rendre le rejeu exact idempotent et rollbacker toute divergence.
5. Ne pas choisir la tâche suivante avant le commit durable.
6. N’utiliser ni JSON/JSONL, ni Dispatcher, ni EventBus comme autorité.
7. VisPy reste observation-only.
