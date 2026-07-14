# 0285-r5 — Historique durable de croissance des capacités

## Décision

La croissance d'un spécialiste devient durable uniquement après une décision opérateur
`approve` produite par le gate 0285-r4. La révision portable complète, la décision et
les empreintes de corrélation sont enregistrées dans un historique append-only adressé
par `sql_ref`.

SQL reste l'autorité durable. Qdrant ne peut recevoir ultérieurement qu'une projection
de rappel contenant des références vers l'autorité SQL. La présence d'une révision dans
l'historique ne la sélectionne pas automatiquement pour le Scheduler et ne déclenche
aucune exécution de laboratoire.

## Réutilisation

Le patch compose sans les dupliquer :

- `SpecialistCapabilityGrowthDecision` de 0285-r4 ;
- `PortableSpecialistRevision` et `SpecialistRevisionLineage` de 0285-r3 ;
- l'identité stable et le descripteur portable de 0284-r2.

## Contrats

- `SpecialistCapabilityGrowthHistoryAppendCommand` lie la lignée de base, la révision
  candidate, la décision approuvée, un compteur optimiste et le futur `sql_ref`.
- `SpecialistCapabilityGrowthHistoryEntry` conserve la révision complète, la décision,
  la lignée résultante et leurs digests.
- `SpecialistCapabilityGrowthHistorySnapshot` valide la continuité de la chaîne.
- `SpecialistCapabilityGrowthHistoryPort` définit la frontière destinée à un adaptateur
  SQL réel.
- `DeterministicSpecialistCapabilityGrowthHistoryAdapter` fournit uniquement un support
  mémoire déterministe pour les tests. Il annonce `durable=False` et n'effectue aucune
  écriture SQL.

## Invariants

1. seules les décisions `revision_authorized=True` sont enregistrables ;
2. le digest de la lignée de base doit correspondre à la décision opérateur ;
3. la révision doit étendre exactement la tête courante ;
4. les numéros d'entrée sont contigus et commencent à 1 ;
5. `entry_ref`, `sql_ref`, `decision_ref` et `revision_ref` sont uniques ;
6. une répétition strictement identique est idempotente ;
7. une collision de référence avec un contenu différent est refusée ;
8. le compteur attendu protège contre les écritures concurrentes obsolètes.

## Frontières

Cette phase ne contient aucun import ou appel SQLite/PostgreSQL, Qdrant, OpenVINO,
Scheduler, laboratoire, EventBus ou GitHub. L'adaptateur SQL DB-API réel sera introduit
séparément après audit des stores existants ; le Scheduler restera l'unique autorité de
sélection et d'orchestration.

## Vérification du bundle Projects

`templates/github/projects-repository/INSTALLATION.md` a été relu. aucune modification
n'est nécessaire : 0285-r5 n'ajoute ni workflow, formulaire, champ ProjectV2, variable,
secret, permission ou procédure de déploiement dans `newicody/projects`.

## Suite

Le prochain jalon est
`0285-r6-specialist-approved-revision-scheduler-selection-contract`. Il définira la
sélection explicite d'une révision durable approuvée par le Scheduler existant, sans
nouveau registre global ni orchestrateur parallèle.
