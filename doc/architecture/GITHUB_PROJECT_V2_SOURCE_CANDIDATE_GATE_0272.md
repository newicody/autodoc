# Gate opérateur des SourceCandidate ProjectV2 — 0272-r7

## Décision

0272-r7 réutilise le contrat de décision `SourceCandidate` existant pour appliquer
une décision locale explicite à une candidate issue d'un lot r6.

```text
handoff batch r6
-> candidate_id
-> SourceCandidateDecision existante
-> immutable local gate record
-> future durable consumer r8
```

Aucun nouveau manager ou orchestrateur n'est ajouté.

## Actions supportées

```text
inspect   -> analyzed, durable ingestion closed
relaunch  -> analyzed, durable ingestion closed
reject    -> rejected, durable ingestion closed
archive   -> archived, durable ingestion closed
promote   -> promoted, future durable ingestion allowed
merge     -> merged, future durable ingestion allowed + target_context_id required
```

L'autorisation produite par `promote` ou `merge` n'est pas une écriture. R7
conserve `sql_write_allowed=False`, `qdrant_write_allowed=False` et
`durable_ingestion_performed=False`. R8 devra consommer explicitement le record.

Un item ProjectV2 retiré est advisory et ne peut pas être promu ou fusionné.

## Mode Project-native

La correction r7 sépare le chemin principal du pont Actions :

- ProjectV2 direct est obligatoire et query-only ;
- le dépôt externe d'Issues et GitHub Actions sont optionnels ;
- `require_actions_deployment=false` permet un readiness vert sans Actions ;
- `--check-actions-bridge` vérifie explicitement le pont secondaire.

## Effets

Le cœur est pur. La CLI lit un lot r6 et écrit :

- un gate record immuable adressé par contenu ;
- un rapport opérateur atomique.

Elle n'effectue aucun appel réseau, aucune écriture SQL/Qdrant, aucune mutation
GitHub et aucune modification Scheduler/SHM.

## État d'intégration

```text
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
