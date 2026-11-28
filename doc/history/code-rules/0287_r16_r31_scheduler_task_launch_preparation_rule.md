# Règle r16-r31 — application d’une admission Scheduler

1. Appliquer uniquement une décision `admitted` encore valide.
2. Résoudre exactement `command_type + capability_ref + contract_version`.
3. Vérifier les politiques de ressources et de reprise du handler.
4. Produire une transition typée `ready → running` et une tentative corrélée.
5. Appliquer la priorité effective décidée par le plan.
6. Charger le budget par un objet typé borné.
7. Exiger une transaction atomique pour budget, réservation, tâche, tentative,
   transition et état de commande.
8. Refuser tout reçu transactionnel divergent.
9. Retourner un ticket typé et immuable avant toute construction de handler.
10. Ne jamais instancier ou exécuter un handler dans cette unité.
11. Ne pas appeler le Dispatcher ou l’EventBus.
12. Ne créer aucune file JSON ou JSONL ; PostgreSQL reste l’autorité durable.
13. Ne publier `CREATED` et `STARTED` qu’après création réelle du handler dans
    l’unité d’exécution suivante.
14. VisPy reste observation-only et ne modifie jamais l’admission.
