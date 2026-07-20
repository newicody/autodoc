# Adaptateur explicite ControlProxy → Scheduler — 0287 r16 r43

## Problème observé

Le handler `SCHEDULER_ROUTE_REQUEST` cherchait déjà en premier le module
`runtime.controlproxy_scheduler_adapter`, mais ce module n'existait pas. Le
module historique `runtime.scheduler_route_adapter` existe, mais sa fonction
exige explicitement `controlfs_root` et `runtime_root` et suppose qu'un manifeste
de route désirée a déjà été accepté. L'appeler directement avec le seul payload
du Scheduler aurait donc masqué deux dépendances et échoué à la frontière
suivante.

## Raccordement retenu

L'unité ajoute uniquement le module déjà prévu par le resolver. Il reçoit la
commande de route déjà autorisée, exige `AUTODOC_CONTROLFS_ROOT`, prépare la
racine de données existante `/dev/shm/autodoc/routes-runtime`, écrit de manière
create-only le manifeste ControlFS désiré, puis délègue à l'adaptateur 0086.

```text
Scheduler canonique unique, déjà actif
    → EventType.SCHEDULER_ROUTE_REQUEST
    → ControlProxySchedulerRouteRequestHandler
    → runtime.controlproxy_scheduler_adapter
        → ControlFS explicite
        → sizing typé par controlproxy_prepare
        → manifeste désiré idempotent
        → runtime.scheduler_route_adapter
        → handshake + lease de route
    → réponse typée au Scheduler
```

La route transporte uniquement des références et des petits messages de
contrôle. Les objets lourds restent dans PostgreSQL ou leurs backends déclarés.
La taille est décidée par la politique de zone `scheduler`; elle n'est pas un
budget d'inférence et ne change aucune priorité du Scheduler.

## JSON et autorités

Le manifeste JSON est une projection temporaire de la surface déclarative
ControlFS. Il n'est ni une file Scheduler, ni un graphe durable, ni une autorité
métier. Aucune file JSONL n'est écrite par ce raccordement; la publication du
faux bus historique est désactivée. PostgreSQL demeure l'autorité durable,
Qdrant demeure une projection/rappel et `/dev/shm` demeure le plan de données
rapide et reconstructible.

## OpenRC

Pendant le test `tool-bounded`, la variable peut être posée dans le shell :

```bash
export AUTODOC_CONTROLFS_ROOT=/dev/shm/autodoc/controlfs
```

Lors du passage au Scheduler `externally-managed`, OpenRC portera la même valeur
dans la configuration du service. OpenRC reste l'autorité de processus; il ne
soumet pas les tâches et ne devient pas un orchestrateur métier.

## Invariants

- aucun Scheduler, Dispatcher, EventBus, thread, processus ou daemon ajouté;
- aucune décision d'admission ou de sécurité dans ControlProxy;
- manifeste incompatible rejeté au lieu d'être écrasé;
- racine ControlFS relative ou implicite interdite;
- runtime de route strictement préparé par l'adaptateur `/dev/shm` existant;
- aucune mutation de `Scheduler.run()`, `PolicyEngine`, `PriorityQueue` ou
  `Dispatcher`.
