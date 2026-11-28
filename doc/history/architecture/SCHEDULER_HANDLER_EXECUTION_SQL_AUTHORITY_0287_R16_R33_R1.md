# Autorité SQL de fin d’exécution — 0287 r16-r33-r1

L’issue typée du handler est persistée avec la tentative terminale, la tâche, la transition, le résultat/échec/interruption et la libération des ressources dans une transaction unique. PostgreSQL reste l’autorité durable. Le Scheduler décide seulement après commit de la suite du graphe.

Aucun JSON ou JSONL interne. Aucun Dispatcher, EventBus, laboratoire ou handler supplémentaire. VisPy reste observation-only et projettera ultérieurement les apparitions/disparitions persistantes.
