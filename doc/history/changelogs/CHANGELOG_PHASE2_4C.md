# CHANGELOG — Phase 2.4c

## Objectif

Corriger la vérification des liens DOT après retour utilisateur.

Le test Phase 2.4bis était trop rigide : il imposait une notion de page canonique et de relation parent/enfant qui ne correspond pas à la roadmap réelle. Dans cette roadmap, un lien peut :

- descendre vers un graphe plus précis ;
- remonter vers une vue plus large ;
- pointer transversalement vers un composant situé dans un autre layer ;
- ne pas exister si aucun détail n'est encore défini.

## Changements

- Remplacement de `tests/docs/test_dot_links.py` par un validateur plus simple et plus juste.
- Suppression de la règle “composant connu -> page canonique imposée”.
- Suppression de l'obligation parent -> enfant.
- Conservation d'une seule règle dure : toute `URL="*.svg"` interne doit résoudre vers un fichier `.dot` existant dans `doc/docs/architecture`.
- Si une URL est cassée mais qu'un fichier du même nom existe ailleurs, le test propose le lien relatif attendu.

## DOT corrigés

- `doc/docs/architecture/context/20_context.dot`
- `doc/docs/architecture/context/21_collector.dot`
- `doc/docs/architecture/context/22_reducer.dot`
- `doc/docs/architecture/context/23_snapshot.dot`
- `doc/docs/architecture/context/24_decision_engine.dot`
- `doc/docs/architecture/scheduler/11_dispatcher.dot`
- `doc/docs/architecture/scheduler/12_event_bus.dot`
- `doc/docs/architecture/scheduler/13_priority_queue.dot`
- `doc/docs/architecture/scheduler/14_component_proxy.dot`

Les fichiers plats `scheduler/11_*.dot` à `scheduler/14_*.dot` sont conservés comme redirections lisibles vers les sous-graphes détaillés situés dans :

- `scheduler/dispatcher/11_dispatcher.dot`
- `scheduler/event_bus/12_event_bus.dot`
- `scheduler/priority_queue/13_priority_queue.dot`
- `scheduler/component_proxy/14_component_proxy.dot`

## Validation

```text
PYTHONPATH=src pytest -q
54 passed
```

Aucun changement runtime. Aucun SVG. Aucun script de patch.
