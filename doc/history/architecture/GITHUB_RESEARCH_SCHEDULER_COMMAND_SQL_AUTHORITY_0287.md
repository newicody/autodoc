# Autorité SQL des commandes de recherche GitHub — 0287 r16-r25

## Décision

Une demande GitHub admissible devient une instance de
`GitHubResearchSchedulerCommand`. Elle n'est jamais stockée comme document JSON
interne et n'est jamais déposée dans une file JSONL canonique.

Le JSON reste limité à la frontière GitHub et aux rapports temporaires de CLI :

```text
GitHub JSON
  -> validation de frontière
  -> classes Python immuables
  -> tables PostgreSQL normalisées
  -> reconstruction des mêmes classes
  -> Scheduler local canonique
```

## Modèle de classes

```text
SchedulerCommand
└── AuthorizedSchedulerCommand
    └── GitHubResearchSchedulerCommand
```

La commande spécialisée compose :

- `SchedulerAuthorization` ;
- `GitHubResearchCorrelation` ;
- `GitHubResearchPayload` ;
- `ResearchExecutionBudget` ;
- `SchedulerRouteRequest`.

L'héritage exprime la spécialisation réelle de la commande. La composition
porte les sous-contrats. Aucune métaclasse n'est nécessaire pour cette unité.

## Modèle relationnel

L'adaptateur `DbApiGitHubResearchSchedulerCommandStore` utilise la connexion
DB-API déjà possédée par `LovePostgreSqlAuthorityBinding` et crée les tables :

- `scheduler_commands` ;
- `scheduler_command_authorizations` ;
- `scheduler_command_github_correlations` ;
- `scheduler_command_research_payloads` ;
- `scheduler_command_context_refs` ;
- `scheduler_command_evidence_refs` ;
- `scheduler_command_execution_budgets` ;
- `scheduler_command_route_requests` ;
- `scheduler_command_states`.

Aucune de ces tables ne contient de colonne JSON. Les références multiples sont
des lignes ordonnées et non des tableaux sérialisés.

## Invariants

- `command_ref` et `command_digest` sont immuables et uniques ;
- `policy_decision_id`, `request_id` et `task_id` restent uniques ;
- un seul ordre de recherche est accepté pour un triplet
  `repository / issue_number / run_id` ;
- un rejeu strictement identique retourne `idempotent_replay=true` ;
- une collision provoque un rollback de tout le graphe relationnel ;
- l'état initial est `pending`, version `1` ;
- le Scheduler, le Dispatcher, l'EventBus, le laboratoire et Qdrant ne sont pas
  appelés par l'adaptateur SQL.

## Frontières

```text
r16-r25
  construit la commande typée
  persiste le graphe relationnel
  initialise l'état pending
  s'arrête

r16-r26
  fera réclamer atomiquement une commande pending
  par le Scheduler local canonique déjà actif
```

La file historique `scheduler.route_requests.jsonl` reste uniquement une trace
de compatibilité de r16-r24 et ne participe pas au chemin canonique.
