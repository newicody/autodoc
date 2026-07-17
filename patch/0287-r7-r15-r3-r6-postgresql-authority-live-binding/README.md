# 0287-r7-r15-r3-r6-postgresql-authority-live-binding

Raccordement PostgreSQL live du runtime installé « amour ».

## Portée

- charge paresseusement `psycopg.connect` à la frontière I/O ;
- accepte un connecteur DB-API injecté pour les tests ;
- réutilise `DbApiContextRevisionAuthorityStore` ;
- sélectionne/crée le schéma PostgreSQL configuré ;
- initialise les tables existantes ;
- crée ou rejoue idempotemment `context-revision:love-base` ;
- expose une fermeture idempotente utilisable plus tard comme hook de lease ;
- ne construit ni Scheduler, ni OpenVINO, ni Qdrant.

## Dépendance externe

Le chemin réel requiert `psycopg` v3 dans l'environnement Python installé.
La dépendance est chargée uniquement dans le nouvel adaptateur I/O et ne remonte
pas vers le noyau ou les contrats.

## Base attendue

Le patch s'applique après :

- `488b4c1 r7-r15-r3-r3-r2-runtime-lease-rule-alignment-rebase`
- et peut coexister avec
  `0287-r7-r15-r3-r5-live-runtime-composer-reuse-audit`, qui n'ajoute que des
  fichiers distincts.

## Vérification

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r6-postgresql-authority-live-binding \
  --dry-run \
  --allow-dirty
```

Puis :

```bash
python apply_patch_queue.py \
  --patch 0287-r7-r15-r3-r6-postgresql-authority-live-binding \
  --commit \
  --push \
  --allow-dirty
```
