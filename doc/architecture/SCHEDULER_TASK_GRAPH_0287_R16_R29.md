# Graphe de tâches Scheduler — 0287 r16-r29

## But

Cette unité construit un graphe immuable au-dessus du modèle r16-r28. Le Scheduler peut déterminer quelles tâches deviennent exécutables sans lancer de handler, sans persister et sans modifier sa boucle actuelle.

## Structure

```text
SchedulerTaskGraph
├── SchedulerTask[]
├── SchedulerTaskBarrier[]
├── SchedulerTaskBranchGate[]
├── SchedulerTaskReadinessPlan
└── SchedulerTaskGraphPromotion
```

Les dépendances directes restent portées par `SchedulerTaskDependency`. Les barrières regroupent plusieurs prédécesseurs. Les branches sont explicites grâce aux portes de branche `ANY` et `ALL`.

## Ordre stable

Les tâches candidates sont ordonnées par :

1. priorité effective décroissante ;
2. date de création ;
3. `task_ref`.

Cet ordre stable ne remplace pas les politiques futures d'équité ou de prévention de famine. Il fournit le socle déterministe avant r16-r30.

## Conditions

- `ALL_SUCCEEDED` : tous les membres de la barrière sont `completed` ;
- `ALL_TERMINAL` : tous les membres sont dans un état terminal ;
- branche `ANY` : une règle suffit ;
- branche `ALL` : toutes les règles doivent être satisfaites ;
- les conditions de branche peuvent viser `completed`, `failed`, `cancelled`, `timed-out` ou tout état terminal.

## Sécurité structurelle

Le graphe refuse :

- les références absentes ;
- les commandes parentes divergentes ;
- les doublons ;
- les auto-dépendances ;
- les cycles formés par dépendances, barrières ou branches.

## Frontières

Le plan de readiness reste pur. La promotion produit un nouveau graphe et des `SchedulerTaskMutation` typées. Elle ne les rend pas durables elle-même.

Cette unité n'appelle aucun handler, aucun Dispatcher, aucun EventBus, aucun laboratoire, PostgreSQL, Qdrant, OpenVINO, ControlProxy ou GitHub. PostgreSQL restera l'autorité durable lors de l'unité de store transactionnel des tâches.

## Suite

- r16-r30 : budgets globaux, profils de ressources, équité, timeout/retry/backoff ;
- r16-r31 : exécuteur contrôlé de handlers ;
- r16-r32 : préparation réelle d'une visite de laboratoire.
