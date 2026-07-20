# Fabrique des ports durables OpenRC — 0287 r16-r61

Cette unité ajoute la frontière typée entre la fondation installée r16-r59 et le
bundle de ports durables r16-r60. Elle ne rouvre aucun backend et interdit aux
composants injectés de posséder une seconde pile d'exécution.

Le Scheduler canonique unique reste l'orchestrateur. PostgreSQL reste l'autorité
durable. Qdrant reste une projection et un moteur de rappel. OpenVINO E5 reste
injecté avec une dimension de 384. OpenRC possède seulement le processus.

La fabrique valide sept ports : continuation, step runner, première visite,
pipeline groupé, étapes aval, publication/clôture et observations relationnelles.
Chaque port est construit autour de la fondation déjà ouverte.

Aucun stockage interne JSON et aucune file JSONL ne sont introduits. La variable
de la fabrique concrète reste vide tant que les adaptateurs PostgreSQL réels ne
sont pas fournis ; le service échoue alors fermé.
