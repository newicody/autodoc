# Règle r16-r31-r1-r1 — binding SQL du lancement Scheduler

1. Réutiliser exactement la connexion possédée par `LovePostgreSqlAuthorityBinding`.
2. Ne créer aucune connexion, aucun pilote, aucun pool et aucun runtime supplémentaire.
3. Initialiser le schéma de lancement au bootstrap PostgreSQL existant.
4. Exposer `DbApiSchedulerTaskLaunchTransaction` comme port typé du binding.
5. Conserver une seule autorité de fermeture pour la connexion partagée.
6. Ne pas démarrer le Scheduler et ne pas instancier ou exécuter de handler.
7. Ne pas produire de notice de cycle de vie avant création réelle du handler.
8. Ne pas appeler Dispatcher, EventBus, laboratoire, Qdrant ou GitHub.
9. Ne stocker aucune autorité en JSON ou JSONL.
10. VisPy reste observation-only et ne modifie aucune transaction.
