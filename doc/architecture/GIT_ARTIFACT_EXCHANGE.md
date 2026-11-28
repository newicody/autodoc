# Transport Git du cadrage scientifique Copilot–serveur

## Décision

Les échanges de cadrage sont réalisés exclusivement par des artefacts versionnés
dans le dépôt Git de gestion des recherches. Chaque producteur écrit un nouveau
fichier, crée un commit et pousse ce commit. L'autre côté observe/récupère le
nouvel artefact depuis Git. Il n'existe aucun appel RPC ou canal direct de
messages Copilot–serveur.

Les artefacts Git constituent le canal asynchrone et la trace append-only du
cadrage. PostgreSQL reste l'autorité durable de l'état métier. Les artefacts
GitHub Actions restent un transport temporaire du workflow existant et ne
remplacent pas le transport Git du cadrage.

## Chemins canoniques

Pour une Issue et un cycle donnés :

- `autodoc/exchanges/issues/<issue>/cycles/<cycle>/copilot-initial.json`
- `autodoc/exchanges/issues/<issue>/cycles/<cycle>/server-response.json`
- `autodoc/exchanges/issues/<issue>/cycles/<cycle>/copilot-refined.json`

Ils résident dans le dépôt de gestion Projects (actuellement
`newicody/projects`). Le cycle est déterminé par la filiation durable de la
recherche, jamais par un timestamp ou un numéro de run Actions.

## Séquence et raccordements présents

1. `issues.opened` déclenche le workflow initial existant. Après génération
   de l'avis Copilot v2, il le publie dans Git avec
   `AUTODOC_EXCHANGE_GIT_TOKEN`. Le commentaire Issue existant reste une
   projection lisible, pas le canal de transport.
2. Le serveur récupère l'artefact initial et construit une évaluation structurée
   à partir de ses propres observations vérifiées. L'adaptateur
   `tools/publish_git_exchange_server_response.py` valide cette évaluation,
   la lie à l'avis initial et pousse `server-response.json`.
3. Le workflow `autodoc-copilot-refinement.yml` ne réagit qu'au push de
   `server-response.json`. Il récupère les deux artefacts, demande une seule
   reformulation à Copilot, puis pousse `copilot-refined.json`. Le push de
   l'artefact reformulé ne déclenche pas ce workflow.
4. Le serveur peut récupérer les trois enveloppes. L'assembleur
   `tools/assemble_fetched_github_research_admissibility_0287.py` accepte
   `--git-exchange-branch` et
   `--require-scientific-framing-exchange`. Il vérifie la chaîne, vérifie que
   l'avis initial Git correspond à l'avis du run Actions et transmet la
   reformulation au work package existant comme indication non autoritative.

Le lancement d'exécution reste distinct : la transition ProjectV2 vers
`En cours` et l'admission du Scheduler gardent leur rôle. La présence d'un
artefact ne déclenche jamais une tâche.

## Contrats, intégrité et sécurité

Le contrat `missipy.github.git_artifact_exchange_envelope.v1` lie le dépôt,
l'Issue, le cycle, le rôle, le producteur, l'horodatage, le payload, son digest
SHA-256, le chemin canonique et les références/digests de l'artefact précédent.
Le commit Git donne l'identité immuable de la révision ; son SHA ne doit pas
être inscrit dans le contenu du fichier qu'il contient.

Un chemin existant avec le même digest est un replay idempotent. Un chemin
existant avec un contenu différent est une collision : il est interdit de
l'écraser. Une correction nécessite une nouvelle révision/cycle et une filiation
explicite.

Les artefacts Copilot restent non fiables et non autoritatifs. La demande
GitHub d'origine reste la demande autoritative ; la reformulation est ajoutée
au work package comme indication. La réponse serveur distingue capacités
vérifiées, limites, données manquantes, provenance et fraîcheur. Aucun artefact
ne donne le droit d'exécuter une tâche.

Le workflow utilise un secret `AUTODOC_EXCHANGE_GIT_TOKEN` limité au dépôt
Projects et à `Contents: read/write`. Le token automatique du workflow reste
en lecture pour les contenus. Le secret historique
`AUTODOC_ISSUE_COMMENT_TOKEN` conserve son usage distinct. Aucun secret n'est
écrit dans Git.

## Limites d'intégration restantes

Les adaptateurs et workflows sont présents dans la branche de développement,
mais le parcours complet n'est pas encore démontré en exploitation :

- le serveur doit encore alimenter l'évaluation à partir des interfaces d'état
  réelles des composants ; l'adaptateur de réponse reçoit actuellement un
  JSON d'évaluation et ne collecte pas lui-même les capacités ;
- l'appel de cet adaptateur doit être raccordé au traitement serveur vivant,
  sans créer de worker ou d'orchestrateur parallèle ;
- l'assembleur d'admissibilité sait exiger la chaîne Git, mais son option doit
  être activée dans le parcours réel déclenché par `En cours` ;
- les permissions, le secret et les workflows doivent être installés dans
  `newicody/projects`, puis le flux doit être vérifié de bout en bout.

Les tests ajoutés ne sont pas déclarés exécutés. Aucun producteur serveur
autonome, collecteur de capacités ou dispatch Scheduler supplémentaire n'est
revendiqué par ce patch.
