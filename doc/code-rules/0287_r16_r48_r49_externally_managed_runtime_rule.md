# Règle 0287 r16-r48-r49 — runtime externe et mémoire temporelle passive

1. OpenRC reste l'autorité de cycle de vie du processus serveur.
2. Le Scheduler existant est l'unique autorité d'orchestration.
3. Un tick réclame au plus une commande et exécute un nombre borné de tâches.
4. Le bootstrap doit exposer exactement dix handlers et dix capacités.
5. Les notices sont tamponnées pendant le métier et persistées après son commit.
6. Une panne d'observation ne modifie jamais l'issue durable d'une tâche.
7. Les traces temporelles sont relationnelles et ne contiennent aucun JSON.
8. PassiveSupervisor et VisPy restent des lecteurs sans autorité.
9. Aucun thread, daemon, manager, Scheduler ou EventBus parallèle n'est créé.
10. Le préfixe de l'issue d'exécution reste `handler-outcome:`.
