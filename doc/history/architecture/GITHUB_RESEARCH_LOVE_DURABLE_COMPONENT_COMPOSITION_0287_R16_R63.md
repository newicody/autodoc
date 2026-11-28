# Composition durable des composants OpenRC — 0287 r16-r63

Cette unité raccorde réellement le store d'observation PostgreSQL construit
par r16-r62 à la fabrique durable r16-r61. La même connexion possédée par la
fondation est réutilisée et aucune seconde autorité SQL n'est ouverte.

Les six composants d'exécution restants sont fournis ensemble : store de
continuation, step runner, première visite, pipeline groupé, étapes aval et
publication/clôture. Leur fabrique reçoit la fondation, la frontière
PostgreSQL et le port partagé ; elle ne peut donc pas justifier un backend
parallèle.

Le Scheduler canonique unique reste l'orchestrateur. PostgreSQL reste
l'autorité durable, Qdrant reste projection et rappel, OpenVINO E5 conserve
la dimension 384 et OpenRC possède uniquement le processus.

Aucun stockage interne JSON et aucune file JSONL ne sont introduits. Le
service échoue fermé tant que la fabrique d'exécution concrète n'est pas
explicitement installée.
