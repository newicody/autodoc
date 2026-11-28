# Règle 0287 r16-r45/r16-r47 — publication et clôture

- Réutiliser le planner, le publisher et la preuve SQL existants.
- Reconstruire le plan depuis l'autorité durable avant publication.
- Exiger approbation, digest exact et trois verrous distants.
- Grouper mutation distante et preuve SQL pour garantir une reprise idempotente.
- Faire de la dernière tâche une relecture sans nouvelle mutation.
- Conserver PostgreSQL comme autorité et GitHub/ProjectV2 comme projections.
- Enregistrer explicitement dix handlers au bootstrap.
- Ne créer aucun Scheduler parallèle, manager, daemon, Dispatcher ou EventBus.
- Ne pas introduire de JSONL, de file interne ou d'état caché entre handlers.
- Garder PassiveSupervisor et VisPy strictement observation-only.
