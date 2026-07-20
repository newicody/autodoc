# Rejeu Qdrant et horodatage SQL initial — 0287 r16 r54

## Problème observé

Les références `vector-projection:*` et `qdrant-point:*` sont déterministes à
partir de l'objet SQL, de son digest, de la révision et de la collection. Lors
d'un nouveau `prepare`, le même couple d'analyses recevait cependant un nouveau
`projected_at`. La projection Qdrant était réinscriptible, mais PostgreSQL
refusait à juste titre la nouvelle métadonnée sous la même référence immuable.

## Décision

Le plan des deux projections relit d'abord leurs métadonnées dans PostgreSQL.
Lorsqu'une projection existe, son `projected_at` devient l'horodatage de première
matérialisation de la paire. Le plan de rejeu et ses digests sont ainsi reconstruits
à l'identique avant toute inférence OpenVINO ou écriture Qdrant.

Un état partiel est complété avec ce même horodatage. Si les deux projections
existantes portent des dates différentes, ou si une identité déterministe ne
correspond plus au contenu SQL, au modèle, à la collection, au vecteur nommé ou
au point Qdrant attendu, l'exécution échoue fermée.

## Réutilisation

L'identité de projection est extraite du projecteur existant dans une fonction
pure prenant les références typées, le digest SHA-256, la révision et la
collection. Le projecteur concret conserve son contrôle strict des classes métier
et délègue ensuite à ce calcul commun. Le plan de paire peut ainsi réutiliser les
objets déjà autorisés par son port SQL, y compris les doubles légers de tests,
sans dupliquer la formule de digest.

## Frontières conservées

- PostgreSQL reste l'autorité durable des métadonnées immuables ;
- Qdrant reste une projection reconstructible et sans corps autoritatif ;
- les deux analyses restent deux points et deux métadonnées distincts ;
- E5 reste en dimension réelle 384 ;
- aucun second Scheduler, Dispatcher, daemon, thread ou processus ;
- aucune file JSONL et aucun JSON comme stockage interne ;
- le JSON de digest reste une représentation canonique de frontière seulement.
