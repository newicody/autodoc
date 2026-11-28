# Transport Git du cadrage scientifique Copilot–serveur

## Décision

Les échanges de cadrage sont réalisés exclusivement par des artefacts versionnés
dans le dépôt Git de gestion des recherches. Chaque producteur écrit un nouveau
fichier, crée un commit et pousse ce commit. L'autre côté observe/récupère le
nouvel artefact depuis Git. Il n'existe aucun appel RPC, webhook direct ou canal
de messages Copilot–serveur.

Les artefacts Git constituent le canal asynchrone et la trace append-only du
cadrage. PostgreSQL reste l'autorité durable de l'état métier. Les artefacts
GitHub Actions peuvent servir aux transferts temporaires du workflow existant,
mais ne constituent pas le transport de cet échange.

## Chemins canoniques

Pour une Issue et un cycle donnés, les trois fichiers sont :

`autodoc/exchanges/issues/<issue>/cycles/<cycle>/copilot-initial.json`
`autodoc/exchanges/issues/<issue>/cycles/<cycle>/server-response.json`
`autodoc/exchanges/issues/<issue>/cycles/<cycle>/copilot-refined.json`

Ils résident dans le dépôt Git de gestion Projects (actuellement `newicody/projects`).
Le numéro de cycle est déterminé par la filiation durable de la recherche ; il
n'est pas déduit du timestamp ni du numéro de run Actions.

## Séquence d'échange

1. Copilot produit `copilot-initial.json` et pousse un commit.
2. Le serveur récupère ce commit, vérifie l'artefact et les références, examine
   les données/capacités/contraintes qu'il peut effectivement lire, puis produit
   `server-response.json` et pousse un commit.
3. Le workflow déclenché par le push de `server-response.json` fait produire
   par Copilot `copilot-refined.json` et pousse un commit.
4. Le serveur récupère `copilot-refined.json`, vérifie la chaîne et présente
   la demande au contrôle d'admission existant du Scheduler.

L'échange de cadrage initial s'arrête après le troisième artefact. Aucun push
de réponse serveur ne doit déclencher une nouvelle réponse serveur ; aucun push
de reformulation ne doit relancer le cadrage initial.

## Intégrité et append-only

Chaque enveloppe contient le dépôt, l'Issue, le cycle, le rôle, le producteur,
l'horodatage, le payload, son digest SHA-256, le chemin canonique et les
références/digests de l'artefact précédent. Le commit Git donne l'identité
immuable de la révision ; son SHA ne doit pas être inscrit dans le contenu du
fichier qu'il contient.

Un chemin existant avec le même digest est un replay idempotent. Un chemin
existant avec un contenu différent est une collision : il est interdit de
l'écraser. Une correction nécessite une nouvelle révision/cycle et une filiation
explicite.

Les artefacts Copilot restent non fiables et non autoritatifs. La réponse
serveur décrit ce qu'il peut vérifier, sans transformer les données manquantes
ou périmées en capacités disponibles. Aucun artefact ne donne le droit
d'exécuter une tâche.

## Raccordements runtime encore requis

Le contrat 0294 définit chemins, enveloppes, filiation, digest et détection de
rejeu/collision. Il ne pousse pas lui-même les commits et ne déclenche pas
encore le workflow de reformulation. Les raccordements à réaliser en réutilisant
les frontières existantes sont :

- publication Git du premier artefact Copilot depuis le workflow de création ;
- lecture serveur du nouvel artefact Git ;
- production et push serveur de la réponse ;
- workflow `push` filtré sur `server-response.json` ;
- publication Git par Copilot de la demande reformulée ;
- récupération serveur et passage au contrôle d'admission existant.

Les permissions d'écriture doivent être limitées au dépôt et aux chemins
nécessaires. Les secrets ne sont jamais inscrits dans les artefacts ou dans Git.
Aucun nouveau manager, queue, bus, worker résident ou orchestrateur n'est créé.
