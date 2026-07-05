# 0104 — ControlProxy route runtime handler binding

0104 amincit le raccord Scheduler-facing de ControlProxy sans modifier le micro-kernel.

La décision verrouillée par 0101/0102 reste inchangée :

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler -> RouteRuntimeManager
```

## Responsabilités

- Scheduler: boucle, temps, queue et priorité.
- PolicyEngine: admission minimale avant queue.
- PriorityQueue: ordre déterministe.
- Dispatcher: `EventType -> Handler` seulement.
- Handler: adaptation mince entre l'événement/requête Scheduler et une capacité.
- RouteRuntimeManager: travail runtime route/ControlFS/mmap/eventfd.
- Specialist branch: logique métier / raisonnement / transformation.
- EventBus: observation seulement.
- Route mmap/eventfd: data plane, pas EventBus.

## Ce que 0104 ajoute

`src/runtime/controlproxy_route_runtime_handler.py` fournit une fonction injectable dans
`ControlProxySchedulerRouteRequestHandler` :

```text
build_controlproxy_route_runtime_request_handler(manager)
```

Ce callable lit une enveloppe Scheduler/policy/zone déjà présente, extrait une
`RoutePrepareDecision`, vérifie que l'enveloppe et la décision ciblent la même route et la
même zone, puis appelle :

```text
RouteRuntimeManager.handle_prepare_decision(decision)
```

## Invariants verrouillés

- Handler remains an adapter thin enough to call RouteRuntimeManager.
- RouteRuntimeManager owns route runtime work.
- Dispatcher remains EventType -> Handler only.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or PolicyEngine modification.
- ControlProxy does not manage global priorities.
- ControlProxy does not decide policy or zone authority.
- No EventBus creation and no bus duplication.
- Route mmap/eventfd is a data plane, not EventBus.
- Specialist branch owns business logic.
- Compatibility wrappers remain temporary adapters.

## Pourquoi ce n'est pas un Scheduler bis

Le binding 0104 ne calcule pas la priorité, ne choisit pas une policy, ne dépile aucune queue,
ne possède aucun bus et ne pilote aucun spécialiste. Il reçoit uniquement un payload déjà passé
par le chemin Scheduler/Policy/Queue/Dispatcher/Handler, puis délègue l'effet runtime route au
manager.

## Rapport `code_rule.md`

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0104 applique la règle existante du chemin noyau et ne crée pas de nouvelle technique de programmation.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
```
