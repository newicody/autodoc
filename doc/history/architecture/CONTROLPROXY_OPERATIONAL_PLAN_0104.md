# ControlProxy operational plan — 0104

0104 remplace la direction risquée du coordinateur scheduler-like par un raccord mince :

```text
Dispatcher
-> ControlProxySchedulerRouteRequestHandler
-> build_controlproxy_route_runtime_request_handler(manager)
-> RouteRuntimeManager.handle_prepare_decision()
```

## Décision de plan

Le futur bloc principal reste `RouteRuntimeManager`, pas `ControlProxyRouteCoordinator`.

Le handler n'est pas le lieu de la logique route. Le handler doit seulement :

1. recevoir le payload porté par le Scheduler/Dispatcher ;
2. vérifier que l'enveloppe de filtrage dispatch est présente ;
3. extraire une `RoutePrepareDecision` ;
4. déléguer au `RouteRuntimeManager`.

## Compatibilité

Compatibility wrappers remain temporary adapters.

Les helpers issus des phases précédentes peuvent rester provisoirement :

```text
prepare_route_for_scheduler()
handle_scheduler_route_request()
ControlProxySchedulerRouteRequestHandler
```

Mais leur direction doit converger vers le binding 0104 puis vers le manager runtime.

## Invariants opérationnels

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

## Prochaine phase

0105 doit clarifier priorités/admission : priorité numérique portée par l'événement, admission minimale par PolicyEngine, ordre déterministe par PriorityQueue. ControlProxy ne doit pas recalculer les priorités globales.
