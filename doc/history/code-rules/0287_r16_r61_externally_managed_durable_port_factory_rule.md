# Règle 0287 r16-r61 — fabrique de ports durables OpenRC

- Réutiliser exactement la fondation r16-r59 déjà ouverte.
- Ne construire aucun Scheduler, Dispatcher, EventBus ou backend supplémentaire.
- Exiger sept ports typés et une preuve d'installation.
- Conserver PostgreSQL comme autorité durable et Qdrant comme projection/rappel.
- Conserver la dimension OpenVINO E5/Qdrant à 384.
- Interdire tout stockage interne JSON et toute file JSONL.
- Échouer fermé si la fabrique concrète n'est pas explicitement configurée.
