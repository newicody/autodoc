# 0284-r1-r5-projects-installation-copilot-safe-default

Base auditée : `5a5e08a` (`master`).

Patch documentaire unitaire. Il aligne le guide cumulatif du bundle
`newicody/projects` sur le workflow déjà présent : Copilot désactivé au premier
déploiement, activation explicite après validation, authentification éphémère
et avis non bloquant.

Le patch ne modifie aucun workflow exécutable, Scheduler, backend SQL/Qdrant,
OpenVINO, EventBus ou route `/dev/shm`.
