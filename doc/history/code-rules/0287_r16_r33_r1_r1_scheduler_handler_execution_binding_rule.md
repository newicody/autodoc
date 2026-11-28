# Règle r16-r33-r1-r1 — binding SQL de fin d’exécution

1. Réutiliser exactement la connexion possédée par `LovePostgreSqlAuthorityBinding`.
2. Ne créer aucune connexion, aucun pilote, aucun pool et aucun runtime supplémentaire.
3. Initialiser le schéma de fin d’exécution au bootstrap PostgreSQL existant.
4. Exposer `DbApiSchedulerHandlerExecutionTransaction` comme port typé du binding.
5. Conserver une seule autorité de fermeture pour la connexion partagée.
6. Ne pas rejouer le handler et ne pas choisir la tâche suivante.
7. Ne pas recalculer le graphe, promouvoir une tâche ou décider d’un retry.
8. Ne pas appeler Dispatcher, EventBus, laboratoire, Qdrant ou GitHub.
9. Ne stocker aucune autorité en JSON ou JSONL.
10. VisPy reste observation-only et ne modifie aucune transaction.
