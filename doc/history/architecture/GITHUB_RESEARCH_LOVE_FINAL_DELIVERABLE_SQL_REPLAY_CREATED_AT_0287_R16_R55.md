# Rejeu du livrable final SQL et horodatage initial — 0287 r16 r55

## Problème observé

Le livrable final possède des références déterministes dérivées du paquet de
travail, de la synthèse de liaison, du plan SQL des deux analyses et du contenu
canonique du paquet final. Lors d'une relance de `prepare`, l'objet d'autorité
reste donc identique, mais l'artefact et la révision recevaient le nouvel
horodatage de la tentative. PostgreSQL rejetait alors correctement les deux
écritures sous les mêmes références immuables.

## Décision

Avant de construire l'artefact et la révision, le plan relit dans l'autorité SQL
les entités finales déjà présentes. Leur premier `created_at` devient
l'horodatage canonique du rejeu.

- aucune entité existante : l'horodatage demandé est utilisé ;
- artefact ou révision déjà présent : son horodatage initial est conservé ;
- artefact et révision présents avec le même horodatage : rejeu exact ;
- horodatages divergents : échec fermé avant toute écriture.

L'objet final, l'artefact et la révision restent comparés par leur mapping complet.
L'immuabilité PostgreSQL n'est donc pas relâchée : le plan est
reconstruit à l'identique avant la comparaison existante.

## Frontières conservées

- PostgreSQL reste l'autorité durable ;
- le Scheduler canonique unique reste l'autorité d'orchestration ;
- Qdrant reste une projection et n'est pas consulté par cette unité ;
- aucun stockage JSON ou file JSONL n'est introduit ;
- aucune mutation GitHub ou ProjectV2 n'est effectuée ;
- aucun Scheduler, Dispatcher, EventBus, thread ou processus supplémentaire
  n'est créé.
