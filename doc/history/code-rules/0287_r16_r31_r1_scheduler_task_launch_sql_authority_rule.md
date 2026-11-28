# Règle r16-r31-r1 — commit SQL d’un lancement Scheduler

1. Réutiliser la connexion DB-API possédée par le binding PostgreSQL local.
2. Refuser l’autocommit et ouvrir aucun pilote dans l’adaptateur.
3. Exiger une commande `claimed` ou déjà `running`, possédée par le même Scheduler.
4. Comparer les versions et digests avant toute mutation durable.
5. Enregistrer budget, ressources, tâche, tentative, transition et commande dans une transaction atomique.
6. Rollbacker toutes les écritures au moindre conflit.
7. Rendre le rejeu exact idempotent par le reçu transactionnel immuable.
8. Stocker les objets dans des tables relationnelles normalisées, sans JSON ni JSONL.
9. Ne pas instancier ou exécuter de handler.
10. Ne pas appeler le Dispatcher, l’EventBus, un laboratoire ou Qdrant.
11. Ne créer aucun Scheduler, manager, registre global ou boucle autonome.
12. VisPy reste observation-only ; les traces seront projetées dans une unité ultérieure.
