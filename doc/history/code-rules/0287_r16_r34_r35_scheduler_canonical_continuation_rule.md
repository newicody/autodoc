# Règle 0287 r16-r34/r16-r35 — continuation du Scheduler canonique

- Exiger un Scheduler canonique déjà actif ; ne jamais en créer un dans le tick.
- Relire l’autorité PostgreSQL après chaque commit de fin de handler.
- Promouvoir les tâches `ready` par le graphe typé et committer la promotion
  avant l’exécution.
- Borner chaque tick par un nombre explicite d’étapes compris entre 1 et 64.
- Réutiliser le pipeline injecté admission→lancement→handler→fin ; ne pas le
  dupliquer dans la boucle.
- Ne pas appeler un Dispatcher applicatif, ne pas ajouter de manager, daemon,
  file JSON ou JSONL.
- Refuser une étape qui ne fait pas avancer durablement la tâche exécutée.
- Laisser au Scheduler seul le choix de la prochaine tâche.
- Garder EventBus, PassiveSupervisor et VisPy observation-only.
