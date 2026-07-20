# Raccord d'une tâche déjà décidée — r16-r66-r1

## Décision

Le cycle borné du Scheduler canonique choisit une tâche `ready`. Le service de
lancement existant résout ensuite son `SchedulerHandlerBinding` dans le catalogue
des dix handlers. r16-r66 ne duplique aucune de ces responsabilités.

La nouvelle frontière relit seulement :

1. la commande typée par `task.command_ref` dans le store PostgreSQL existant ;
2. le candidat et le plan d'admission déjà décidés et durables ;
3. les ports d'exécution déjà injectés par la composition installée.

Elle remet ensuite au runner r16-r65 le catalogue et la fabrique du bootstrap
complet **par identité**, sans examiner `capability_ref` et sans résoudre un
handler.

## Chaîne d'autorité

```text
SchedulerCanonicalBoundedCycle
  -> task_ref ready déjà choisi
  -> réhydratation commande + admission durable
  -> SchedulerTaskLaunchPreparationService
  -> SchedulerHandlerCatalog déjà assemblé
  -> SchedulerHandlerBinding
  -> ExplicitSchedulerHandlerFactory déjà assemblée
  -> handler
```

## Interdictions

Cette frontière ne crée ni Scheduler, ni Dispatcher, ni EventBus, ni catalogue,
ni fabrique de handlers, ni routeur de capacités. Elle ne planifie pas, ne
réserve pas et ne modifie pas le graphe.

## Étape suivante

r16-r67 fournira les lectures PostgreSQL concrètes de l'admission et les ports
d'exécution génériques, puis raccordera cette frontière à la composition OpenRC.
Les quatre fournisseurs métier restent attachés aux builders explicites des dix
handlers ; ils ne sont jamais sélectionnés par un routeur central.

## Correction r1

Le sink d'information reste un protocole passif inchangé. Les frontières r65 et
r66 vérifient structurellement la présence de `publish` au lieu de modifier le
contrat canonique uniquement pour permettre un `isinstance`.
