# Modèle typé des tâches Scheduler — 0287 r16-r28

## But

Une commande représente une mission durable. Une tâche représente une unité exécutable gouvernée par le Scheduler canonique. Cette unité verrouille le modèle interne avant d'ajouter le planificateur, l'allocation de ressources ou l'exécuteur de handlers.

```text
SchedulerCommand
→ une ou plusieurs SchedulerTask
→ zéro ou plusieurs SchedulerTaskAttempt
→ SchedulerTaskResult ou SchedulerTaskFailure
→ SchedulerTaskTransition durable
```

## Classes

- `SchedulerTask` : identité, commande parente, capacité, version, priorité, état, budget de tentatives, dépendances et références légères ;
- `SchedulerTaskState` : `planned`, `ready`, `running`, `paused`, `retry-wait`, `completed`, `failed`, `cancelled`, `timed-out` ;
- `SchedulerTaskDependency` : prédécesseur et condition `succeeded` ou `terminal` ;
- `SchedulerTaskAttempt` : exécution concrète d'un handler, numérotée et bornée ;
- `SchedulerTaskResult` : résultat typé et digesté ;
- `SchedulerTaskFailure` : erreur typée, preuve et caractère rejouable ;
- `SchedulerTaskTransition` : preuve immuable de chaque changement d'état ;
- bundles de démarrage, réussite et échec : corrélation atomique des objets produits par une décision Scheduler.

## Invariants

- objets gelés et déterministes ;
- aucun dictionnaire ou JSON comme autorité interne ;
- aucune tâche ne dépend d'elle-même ;
- aucun prédécesseur dupliqué ;
- aucune transition depuis un état terminal ;
- `ready → running` exige la création d'une tentative ;
- `running → completed` exige un `SchedulerTaskResult` correspondant ;
- `running → failed/retry-wait` exige un `SchedulerTaskFailure` correspondant ;
- un échec rejouable ne passe à `retry-wait` que si le budget de tentatives le permet ;
- chaque transition incrémente `state_version` et possède un digest.

## Autorités

Le modèle est pur. Il ne démarre aucun Scheduler et ne persiste rien. L'autorité durable future reste PostgreSQL. Le Scheduler décidera des transitions et un store relationnel les enregistrera transactionnellement.

Le Dispatcher, l'EventBus, ControlProxy, le laboratoire, les handlers, Qdrant, OpenVINO et GitHub ne sont pas appelés par ce module.

## Priorités et dépendances

`initial_priority` conserve la valeur d'admission. `effective_priority` peut être recalculée par le Scheduler, avec une nouvelle version et un nouveau digest, sans modifier la priorité historique.

La dépendance `succeeded` exige `completed`. La dépendance `terminal` accepte toute fin, utile pour les barrières, nettoyages ou compensations futures.

## Suite

- r16-r29 : graphe de tâches, ordre stable, barrières et branches ;
- r16-r30 : budgets globaux, profils de ressources, timeout/retry/backoff ;
- r16-r31 : exécuteur contrôlé de handlers et notices informatives ;
- r16-r32 : première tâche réelle de préparation de visite laboratoire.
