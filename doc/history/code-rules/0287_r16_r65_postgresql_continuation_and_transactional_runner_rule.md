# Règle 0287 r16-r65 — continuation et runner transactionnel

- Injecter la connexion DB-API par le port PostgreSQL partagé ; ne jamais ouvrir un driver.
- Enregistrer la topologie du graphe en tables normalisées, sans JSON, JSONL, pickle ou blob métier.
- Relire les tâches depuis les mêmes tables que les transactions de lancement et de clôture.
- Dériver la révision des promotions, lancements et clôtures réellement commis.
- Comparer révision, digest, état et version avant toute promotion.
- Réutiliser les services canoniques de lancement, cycle de vie et exécution des handlers.
- Réutiliser par identité les transactions r31 et r33 imposées par r16-r64.
- Retourner l'outcome typé au cycle canonique ; ne créer aucune décision de tâche suivante.
- Exiger un fournisseur typé pour la commande, l'admission et les ports métier ; échouer fermé sinon.
- Ne créer ni Scheduler, Dispatcher, EventBus, manager, thread, processus ou backend parallèle.
- Ne déclencher aucune mutation GitHub ou ProjectV2 dans cette frontière.
