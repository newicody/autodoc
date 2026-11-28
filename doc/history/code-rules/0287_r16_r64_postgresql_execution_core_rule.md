# Règle 0287 r16-r64 — noyau d'exécution PostgreSQL partagé

- Réutiliser exactement `foundation.postgresql_adapter_port`.
- Construire le store de continuation par `build_adapter` sur la connexion déjà possédée.
- Réutiliser exactement `foundation.task_launch_transaction` et `foundation.handler_execution_transaction`.
- Imposer ces objets après les arguments du constructeur de step runner afin qu'ils ne soient pas remplaçables.
- Exiger `load_snapshot`, `commit_promotion`, `commit_launch`, `commit_outcome` et `run_ready_task`.
- Ne pas exposer la connexion brute et ne pas ouvrir de second backend.
- Ne créer aucun Scheduler, Dispatcher, EventBus, manager, thread ou processus.
- Ne créer aucun stockage métier JSON et aucune file JSONL.
- Laisser Qdrant en projection/rappel et OpenVINO E5 en génération explicite de vecteurs 384.
- Échouer fermé lorsqu'une fabrique est absente, mal formée ou retourne une surface incomplète.
