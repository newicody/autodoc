# Règle 0287 r16 r59 — fondation backend externally-managed

1. La fondation construit exactement un Scheduler canonique unique par processus.
2. PostgreSQL reste l'autorité durable et fournit le command store transactionnel.
3. Qdrant reste une projection et un rappel par références, jamais une autorité.
4. OpenVINO E5 reste réel, local, explicite et dimensionné à 384.
5. Les effets Qdrant exigent des portes d'environnement explicites.
6. Aucun second Dispatcher, EventBus, thread, daemon ou subprocess n'est créé.
7. Aucune file JSONL et aucun stockage interne JSON ne sont autorisés.
8. OpenRC possède uniquement le cycle de vie du processus et les fermetures.
9. Les fournisseurs des dix handlers restent une unité distincte et typée.
