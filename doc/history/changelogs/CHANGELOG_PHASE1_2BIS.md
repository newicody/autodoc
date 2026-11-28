# Changelog — Phase 1.2bis

## Objectif

Remettre le dépôt en conformité avec `doc/code-rules/code_rule.md` sans changer inutilement l'architecture actuelle.

## Changements code

- Reformattage complet des fichiers Python compactés en une ligne.
- Correction de `contracts.component.Component.tick()` en générateur asynchrone abstrait.
- Conservation des contrats immuables avec `dataclass(frozen=True, slots=True)` pour les données structurantes.
- Ajout de `freeze_mapping()` dans `contracts.context` pour produire des snapshots non mutables.
- Correction de `Event.metadata` et `InferenceContext.priorities` pour éviter les factories invalides de `MappingProxyType`.
- Stabilisation du `Dispatcher` : un événement sans handler produit une réponse explicite et ne bloque pas.
- Stabilisation de `PriorityQueue` avec FIFO déterministe à priorité égale.
- Stabilisation de `LifecycleManager` avec états et erreurs observables.
- Stabilisation de `ComponentProxy` : démarrage, arrêt unique, erreur observable, `Request.reply` explicite.
- Correction de `DummyExpert.tick()` en vrai générateur asynchrone.
- Correction de `main.py` et suppression du shebang invalide.

## Changements Context Engine

- Suppression du fast path `ContextEngine -> Registry -> proxy.context()` comme chemin principal.
- Ajout d'une collecte événementielle :

```text
ContextCollector
  -> Event(CONTEXT_REQUEST + Request.reply)
  -> Scheduler.emit()
  -> Dispatcher
  -> ContextRequestHandler
  -> ComponentProxy.context()
  -> Request.reply
  -> EventBus.publish(CONTEXT_REPLY)
  -> ContextReducer
```

## Changements documentation

- Mise à jour de `doc/ARCHITECTURE_LAYERS.md`.
- Ajout de commentaires invisibles dans les DOT modifiés pour expliquer la raison architecturale.
- Aucun SVG généré dans ce lot.
- Aucun script de patch fourni.

## Tests

Commandes exécutées :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
```

Résultat :

```text
7 passed
MAIN_OK
```
