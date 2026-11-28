# Fondation installée du runtime externally-managed — 0287 r16 r59

## But

Ouvrir une seule fois, au démarrage du futur processus OpenRC, les fondations
réelles déjà utilisées par Autodoc : PostgreSQL, OpenVINO E5, Qdrant hybride et
la pile du Scheduler canonique unique.

Cette unité ne prétend pas encore fournir les quatre fournisseurs de
réhydratation ni le store durable de continuation. Elle construit la fondation
process-local qui leur sera injectée dans l'unité suivante.

## Autorités et cycle de vie

- OpenRC possédera le processus.
- Le Scheduler canonique unique reste l'autorité d'orchestration.
- PostgreSQL reste l'autorité durable des commandes, graphes, analyses et preuves.
- Qdrant reste une projection et une surface de rappel par références.
- OpenVINO E5 fournit les embeddings réels en dimension 384.
- ControlFS et `/dev/shm` restent le plan de données rapide.

Les connexions PostgreSQL et Qdrant sont ouvertes une fois et exposent des
callbacks de fermeture possédés par le bundle OpenRC. Aucun backend n'est
recréé à chaque tick.

## Frontière d'effets

Les portes Qdrant restent explicites. Le processus possède une référence de
politique de service `policy:*`; elle autorise les adaptateurs installés mais ne
remplace jamais les décisions typées attachées aux commandes métier.

## Sérialisation

Aucune file JSONL et aucun stockage interne JSON ne sont ajoutés. Les mappings
ne sont que des reçus de frontière. PostgreSQL conserve les objets métier et
les transitions durables sous forme relationnelle.

## Suite

L'unité suivante raccordera cette fondation aux ports durables du cycle borné,
aux fournisseurs de réhydratation des dix handlers et au bundle r16-r58. Le
service OpenRC restera non activé avant un `--check` réel réussi.
