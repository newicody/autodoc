# Règle 0287 r16 r58 — composition installée externally-managed

1. La composition utilise exactement le Scheduler canonique unique injecté.
2. OpenRC possède le processus, pas les décisions métier.
3. PostgreSQL reste l'autorité durable ; aucune file JSONL ne peut le remplacer.
4. Aucun stockage interne JSON ne porte les commandes ou le graphe Scheduler.
5. Qdrant reste projection/rappel et OpenVINO reste un port d'embedding injecté.
6. Le runtime doit cataloguer exactement les dix handlers existants.
7. Le cycle borné doit recevoir ses stores et son step runner explicitement.
8. Aucune PriorityQueue, aucun Dispatcher, aucun EventBus et aucun second
   Scheduler ne doivent être construits dans cette composition.
9. Le mode `externally-managed` est obligatoire et toute divergence échoue fermée.
10. Les fermetures de backends sont possédées par le bundle OpenRC en ordre inverse.
