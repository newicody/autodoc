# Code rule 0287 r16 r56 — digest de publication vers preuve SQL

1. Le digest brut confirmé par l'opérateur ne doit jamais être modifié avant ou
   pendant l'exécution distante.
2. La preuve PostgreSQL doit stocker une référence typée `sha256:*` obtenue par
   ajout du préfixe au même digest hexadécimal de 64 caractères.
3. La normalisation est stricte et fail-closed : aucune valeur arbitraire ne peut
   être re-hachée ou acceptée silencieusement.
4. Le rejeu distant exact doit produire `replay` sans seconde mutation Issue ou
   ProjectV2 avant la clôture SQL.
5. PostgreSQL reste l'autorité durable ; aucune file JSONL et aucun
   stockage interne JSON ne sont introduits.
6. Le Scheduler canonique unique, Qdrant comme projection et OpenRC comme
   autorité externe de processus restent inchangés.
