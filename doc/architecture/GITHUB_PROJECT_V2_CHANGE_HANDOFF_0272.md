# GitHub ProjectV2 change set vers SourceCandidate — 0272-r6

## Décision

La phase 0272-r6 convertit un change set local immuable de 0272-r4 en un lot de
handoffs locaux. Elle réutilise le contrat existant `SourceCandidate` au lieu de
créer une nouvelle représentation d'entrée GitHub.

```text
ProjectV2 query-only
-> snapshot immuable
-> change set local
-> SourceCandidate handoffs
-> future gate opérateur
```

## Audit de réutilisation

Surfaces existantes retenues :

- `context.source_candidate.SourceCandidateInput` ;
- `context.source_candidate.SourceCandidateOrigin` ;
- `context.source_candidate.SourceCandidatePolicy` ;
- `context.source_candidate.build_source_candidate` ;
- le schéma de change set `missipy.github.project_v2_snapshot_change_set.v1`.

Le handoff local 0267 reste une preuve historique d'orientation, mais r6 reçoit
un change set ProjectV2 déjà normalisé plutôt qu'un scan local de dépôt.

Aucun nouveau manager, orchestrateur, worker SQL, adaptateur Qdrant ou client
GitHub n'est ajouté.

## Contrats

Entrée :

```text
missipy.github.project_v2_snapshot_change_set.v1
```

Sortie :

```text
missipy.github.project_v2_change_handoff_batch.v1
  handoffs[]
    missipy.github.project_v2_change_handoff.v1
      candidate: missipy.source_candidate.v1
```

Chaque handoff transporte :

- la nature `added`, `changed` ou `removed` ;
- la référence du change set ;
- l'identité ProjectV2 et item ;
- le titre, le corps et le statut courant ;
- le dépôt/numéro/URL lorsqu'il s'agit d'une Issue ou Pull Request ;
- les chemins modifiés pour un item changé ;
- une `SourceCandidate` déterministe ;
- l'obligation d'une gate opérateur avant ingestion durable.

Une suppression distante est seulement advisory : elle ne supprime jamais un
contexte local et ne demande aucune suppression SQL.

## Baseline

La première comparaison r4 est une baseline. Par défaut, r6 ne transforme pas
les éléments déjà présents en centaines de nouvelles candidates :

```text
include_baseline = false
```

L'opérateur peut l'autoriser explicitement avec `--include-baseline`.

## Budget

La conversion est bornée par :

```ini
[change_handoff]
max_handoffs = 100
```

Les entrées sont triées de façon déterministe, le dépassement est exposé dans
`truncated_count` et aucun traitement caché n'est lancé.

## Effets

Le cœur est pur. La CLI assure seulement :

- lecture du change set ;
- sélection du dernier fichier local ;
- écriture atomique du rapport ;
- écriture immuable du lot de handoffs.

Elle ne contacte pas GitHub et n'accède pas à SQL ou Qdrant.

## État d'intégration

```text
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

La capacité n'est pas encore intégrée au Scheduler. La transition est courte :
0272-r7 ajoutera la gate opérateur, puis r8 réutilisera le chemin durable existant.
