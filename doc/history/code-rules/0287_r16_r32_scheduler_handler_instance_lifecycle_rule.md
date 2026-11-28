# Règle r16-r32 — création et armement des handlers

1. Construire un handler uniquement depuis un ticket de lancement déjà commité.
2. Utiliser une fabrique explicitement injectée; aucun registre global ni effet d'import.
3. Exiger que l'instance corresponde exactement au binding résolu par le Scheduler.
4. Publier `CREATED` seulement après création réelle de l'instance.
5. Publier `STARTED` seulement après validation de la deadline et avant l'exécution.
6. Ne jamais appeler `handler.execute()` dans cette unité.
7. Une panne du sink informatif ne doit jamais annuler une décision Scheduler.
8. Ne pas appeler Dispatcher, EventBus, laboratoire, SQL, Qdrant ou GitHub.
9. Ne créer aucun Scheduler et ne stocker aucune autorité en JSON ou JSONL.
10. Les notices de fin et la fermeture appartiennent à l'exécuteur suivant.
11. VisPy reste observation-only; sa future mémoire temporelle peut agréger les objets temporaires.
