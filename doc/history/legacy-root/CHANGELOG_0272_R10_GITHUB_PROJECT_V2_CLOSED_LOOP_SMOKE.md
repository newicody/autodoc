# Changelog — 0272-r10 ProjectV2 closed-loop smoke

## Added

- composition r7 gate -> r8 SQL -> E5 -> r9 projection -> 0263 recall/rehydrate ;
- replay durable r8 obligatoire et idempotent ;
- `embedding_space_family_ref` partagé par les profils passage/query ;
- validation query avant toute écriture Qdrant ;
- vérification que Qdrant rend le `sql_ref` durable ;
- vérification de la réhydratation SQL ;
- CLI réelle utilisant la membrane Qdrant 0271 avec write+search explicitement autorisés ;
- tests contexte, CLI et règles ;
- architecture, graphe, release, manifest et rapport de tests.

## Boundaries

- SQL reste l'autorité durable ;
- Qdrant reste refs-only pour le recall ;
- aucun embedding externe n'est accepté ;
- aucune mutation GitHub ;
- aucun laboratoire sélectionné ;
- aucune modification de `Scheduler.run()` ou SHM ;
- aucune dépendance non-stdlib ajoutée.

- Correct the existing 0261 query-role propagation required by the closed-loop recall smoke.
