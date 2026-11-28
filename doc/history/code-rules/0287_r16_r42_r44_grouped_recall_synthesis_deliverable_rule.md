# Règle 0287 r16-r42/r16-r44 — rappel, synthèse et livrable

- Réutiliser les compositions existantes de rappel, synthèse et livrable SQL.
- Conserver rappel, synthèse et livrable comme trois tâches distinctes.
- Réhydrater les commandes typées par un port injecté, sans état caché.
- Vérifier le `work_package_ref` après chaque capacité.
- Rappeler des références Qdrant puis réhydrater les corps depuis PostgreSQL.
- Ne jamais fusionner ni modifier les deux analyses sources.
- Persister le livrable local avant toute mutation GitHub.
- Enregistrer explicitement les sept handlers disponibles au bootstrap.
- Ne pas cataloguer encore les capacités de publication ou de clôture.
- Ne créer aucun Scheduler, manager, daemon, Dispatcher ou EventBus parallèle.
- Garder PassiveSupervisor et VisPy observation-only.
