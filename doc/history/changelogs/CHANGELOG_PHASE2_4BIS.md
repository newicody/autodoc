# CHANGELOG — Phase 2.4bis

## Correction

Correction du test de navigation DOT introduit en Phase 2.4.

L'ancien test vérifiait seulement que les URL SVG avaient une source DOT correspondante, avec une erreur de diagnostic quand une URL était résolue hors de `doc/docs/architecture`.
Ce n'était pas suffisant pour la roadmap : le besoin réel est de vérifier la navigation d'architecture.

## Nouveau contrat testé

Le nouveau test vérifie :

- qu'une URL DOT/SVG se résout depuis le fichier DOT qui la contient ;
- que la cible reste dans `doc/docs/architecture` ;
- que la source DOT cible existe ;
- que les `ROADMAP_ID` déclarés sont uniques ;
- qu'un `ROADMAP_PARENT` implique une navigation bidirectionnelle parent/enfant ;
- que les composants connus pointent vers leur page canonique quand une URL est présente.

## DOT corrigés

Les liens suivants pointaient encore vers `scheduler/10_scheduler.svg` alors qu'un sous-graphe canonique existe :

- `ComponentProxy` -> `scheduler/component_proxy/14_component_proxy.svg`
- `PriorityQueue` -> `scheduler/priority_queue/13_priority_queue.svg`
- `Dispatcher` -> `scheduler/dispatcher/11_dispatcher.svg`
- `EventBus` -> `scheduler/event_bus/12_event_bus.svg`

Des commentaires invisibles `ROADMAP_ID` et `ROADMAP_PARENT` ont été ajoutés aux graphes concernés afin que les tests puissent vérifier la remontée/descente de la hiérarchie sans dépendre de la mise en page visuelle.

## Contraintes respectées

- Aucun SVG généré.
- Aucun script de patch.
- Modification uniquement des DOT concernés et du test de navigation.
- Aucun changement runtime Python.
