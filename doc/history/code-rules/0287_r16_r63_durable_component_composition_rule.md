# Règle 0287 r16-r63 — composition durable OpenRC

- Réutiliser exactement la frontière PostgreSQL r16-r62.
- Exiger que le port partagé soit le même objet que celui de la fondation.
- Construire le store d'observation sur la connexion déjà possédée.
- Injecter ensemble continuation, step runner et quatre providers typés.
- Ne créer aucun Scheduler, Dispatcher, EventBus ou backend supplémentaire.
- Conserver PostgreSQL comme autorité durable et Qdrant comme projection/rappel.
- Interdire tout stockage interne JSON et toute file JSONL.
- Échouer fermé sans fabrique d'exécution explicitement configurée.
