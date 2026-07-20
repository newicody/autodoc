# Règle 0287 r16 r60 — liaison des composants OpenRC

1. Ouvrir exactement une fondation installée r16-r59 par processus.
2. Construire les fournisseurs durables uniquement autour de cette fondation.
3. Exiger le même Scheduler canonique unique et la même révision PostgreSQL.
4. Exiger la même collection Qdrant et la dimension OpenVINO E5 de 384.
5. Ne créer aucun backend, Dispatcher, EventBus, thread ou processus parallèle.
6. PostgreSQL reste l'autorité durable ; Qdrant reste projection et rappel.
7. Aucune file JSONL et aucun stockage interne JSON ne sont autorisés.
8. Fermer la fondation en ordre inverse lors d'un échec de composition.
9. OpenRC possède le processus, pas les décisions métier du Scheduler.
10. VisPy et PassiveSupervisor restent observation-only.

code_rule_review: done
code_rule_update_required: true
code_rule_reason: nouvelle liaison explicite entre ressources installées et ports durables des dix handlers.
