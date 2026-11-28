# Règle 0287 r16-r62 — port PostgreSQL partagé

- Réutiliser exactement la connexion possédée par le binding PostgreSQL.
- Interdire l'accès direct à la connexion depuis les composants applicatifs.
- Construire les adaptateurs par un port typé et valider leurs méthodes.
- Vérifier les capacités DB-API au moment de construire l'adaptateur, pas lors de la création du port.
- Laisser le binding seul fermer la connexion.
- Initialiser le store d'observation relationnel sur cette même connexion.
- Ne créer aucun Scheduler, backend, stockage interne JSON ou file JSONL.
- Conserver PostgreSQL comme autorité durable et OpenRC comme autorité de processus.
