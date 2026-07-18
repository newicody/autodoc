# Remise d’une recherche au Scheduler existant

## Objectif

L’unité r16-r9 ferme la première vraie frontière d’exécution locale :

```text
SchedulerRouteRequest autorisé
→ Event SCHEDULER_ROUTE_REQUEST
→ Scheduler.emit()
→ PriorityQueue existante
→ Dispatcher existant
→ ControlProxySchedulerRouteRequestHandler existant
→ réponse de route
```

## Runtime réutilisé

L’appelant fournit les `ImportedActionsRuntimePorts` déjà composés. Ils
contiennent le Scheduler et le Dispatcher réels ainsi que leur attestation.

Cette unité ne construit ni ne démarre aucun composant. Si le Scheduler
existant n’est pas déjà actif, la remise est refusée avec
`scheduler-not-running`.

## Enregistrement du handler

Le Dispatcher existant reçoit
`ControlProxySchedulerRouteRequestHandler` pour le type
`SCHEDULER_ROUTE_REQUEST`.

L’enregistrement est idempotent :

- `registered` au premier raccordement;
- `replay` si le même handler est déjà présent;
- refus si un autre handler occupe ce type d’événement.

## Réponse coopérative

L’événement possède un `Request.reply`. Le Scheduler place l’événement dans sa
queue, le Dispatcher le publie sur l’EventBus d’observation puis appelle le
handler. La réponse est validée contre
`missipy.scheduler.route_adapter_reply.v1`.

## Limites

Cette unité :

- ne modifie pas `Scheduler.run()`;
- ne crée pas de Scheduler, Dispatcher ou EventBus;
- ne lance pas le laboratoire;
- ne lance aucun spécialiste;
- n’écrit ni SQL ni Qdrant;
- ne modifie pas GitHub;
- ne crée aucun daemon;
- conserve l’EventBus en observation seulement.

L’unité suivante transformera la route prête en
`LABORATORY_VISIT_REQUEST` remis au Scheduler existant.
