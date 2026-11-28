# Remise locale d’un intake GitHub autorisé au Scheduler canonique — 0287 r16-r24

> **Statut r16-r24-r1 : chemin non canonique.** La file JSONL reste une
> compatibilité historique, mais la recherche GitHub doit désormais construire
> une commande typée puis la persister dans PostgreSQL. Ne pas utiliser cette
> file comme autorité ou comme chemin serveur réel.

## Décision

Autodoc conserve **un seul Scheduler local canonique**, possédé par le processus serveur.
La commande qui récupère et valide les artefacts GitHub ne démarre pas un Scheduler
éphémère et ne tente pas d’appeler un runtime vivant depuis un autre processus.

La frontière retenue réutilise la file locale existante :

```text
validated fetched triplet
  -> authorized research Scheduler intake
  -> scheduler.route_requests.jsonl
  -> canonical local Scheduler server (unité suivante)
```

## Dispatcher

Le Dispatcher du noyau reste un routeur mécanique interne appelé par
`Scheduler.run()` pour associer un type d’événement à un handler. Il n’est pas une
autorité d’orchestration, ne possède pas de boucle autonome et n’est pas utilisé
par la commande de remise locale r16-r24.

La suppression ou la réduction future de cette mécanique interne ne doit pas être
confondue avec la création d’une couche de dispatch applicative entre l’intake et
le Scheduler.

## Frontières verrouillées

- SQL reste l’autorité durable des résultats et décisions.
- Qdrant reste une projection de rappel.
- EventBus reste une surface d’observation ; il ne transporte pas cette commande.
- La file contient seulement des `SchedulerRouteRequest` déjà autorisées.
- `repository`, `run_id` et `policy_decision_id` sont revérifiés à la remise.
- Un rejeu strictement identique est idempotent.
- Une collision de `request_id` avec un contenu différent est refusée.
- Aucun Scheduler, Dispatcher, EventBus, handler, laboratoire, SQL ou Qdrant n’est
  exécuté par cette unité.

Le consommateur serveur fera l’objet de l’unité suivante : il lira la file sous
l’autorité du Scheduler local déjà actif, remettra la commande au Scheduler et
produira un accusé de consommation durable.
