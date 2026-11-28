# Catalogue explicite des capacités et handlers — 0287 r16-r27

## Audit de réutilisation

`kernel.Registry` reste le registre unique des **instances actives de `ComponentProxy`**. Il porte leur présence dans le runtime et participe au contexte global. Une classe de handler déclarative n'est pas un composant actif : elle n'est ni démarrée, ni arrêtée, ni inspectée comme un `ComponentProxy`.

Mélanger les deux dans `Registry` confondrait :

- identité d'instance et identité de contrat ;
- cycle de vie runtime et description statique ;
- composant actif et classe constructible ;
- contexte observable et capacité résoluble.

L'unité r16-r27 ajoute donc un **catalogue immuable**, pas un nouveau manager, orchestrateur ou registre global. Il est construit explicitement au bootstrap puis injecté au Scheduler.

## Structure

```text
SchedulerHandlerMeta
→ certifie HandlerDescriptor

bootstrap explicite
→ SchedulerHandlerCatalog((HandlerA, HandlerB, ...))

Scheduler
→ resolve(command_type, capability_ref, contract_version)
→ SchedulerHandlerBinding
→ future fabrique injectée
→ future exécution contrôlée
```

La clé exacte est :

```text
command_type + capability_ref + contract_version
```

Aucune sélection implicite de la version la plus récente n'est autorisée. Le plan de tâche Scheduler doit demander une version explicite.

## Invariants

- aucun auto-enregistrement à l'import ;
- aucune variable globale mutable ;
- aucune instance de handler créée ;
- aucune ressource ouverte ;
- aucun appel au Dispatcher ;
- aucun événement EventBus ;
- aucune décision de priorité, retry, budget ou laboratoire ;
- refus d'une clé de capacité dupliquée ;
- refus d'un `handler_ref` dupliqué ;
- correspondance exacte avec le `HandlerDescriptor` certifié par la métaclasse.

## Attributs avancés

Chaque binding expose le descripteur complet :

- politique d'idempotence ;
- références de timeout et retry ;
- profil de ressources ;
- compatibilités de laboratoire ;
- titre, résumé et textes informatifs de cycle de vie.

Ces attributs seront consommés plus tard par le Scheduler et son exécuteur contrôlé. Le catalogue ne les interprète pas dynamiquement.

## Frontière VisPy différée

À la phase finale, les `HandlerLifecycleNotice` et les autres objets temporaires observés devront laisser une trace persistante ou agrégée : apparition, disparition, durée, type et dénombrement. Cette mémoire d'observation appartiendra au read model PassiveSupervisor/VisPy ou à son store dédié ; elle ne deviendra jamais une autorité d'orchestration et ne modifiera pas le catalogue.
