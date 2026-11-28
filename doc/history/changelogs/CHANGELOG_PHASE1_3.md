# Changelog — Phase 1.3

## Objectif

Sortir le pipeline de contexte du noyau `kernel/` tout en conservant le `Context Engine` comme brique fondamentale du micro-kernel.

La Phase 1.3 ne branche pas encore OpenVINO, Qdrant, SQLite ou MCTS.

## Changements code

- Ajout du package `src/context/`.
- Ajout de `ContextCollector`.
- Ajout de `ContextReducer`.
- Ajout de `InferenceContextBuilder`.
- Ajout de `ContextRequestHandler`.
- `ContextEngine` devient un pipeline composé au lieu d'un bloc monolithique.
- `kernel/context_engine.py` devient un shim de compatibilité.
- `Scheduler` déclenche toujours le contexte, mais ne connaît pas les détails de collecte/réduction.
- `Launcher` enregistre explicitement le handler `CONTEXT_REQUEST`.
- `LifecycleManager` ne gère plus les événements de contexte.
- `ComponentProxy.stop()` ne dégrade plus l'état final après arrêt ou erreur déjà émise.

## Flux contexte Phase 1.3

```text
Scheduler context clock
  -> ContextEngine.execute_tick()
  -> ContextCollector.collect()
  -> Event(CONTEXT_REQUEST + Request.reply)
  -> Scheduler.emit()
  -> PriorityQueue
  -> Dispatcher
  -> ContextRequestHandler
  -> ComponentProxy.context()
  -> Request.reply
  -> EventBus.publish(CONTEXT_REPLY)
  -> ContextReducer.reduce()
  -> GlobalContextSnapshot
  -> InferenceContextBuilder.build()
  -> InferenceContext
```

## Changements documentation

- Mise à jour de `doc/ARCHITECTURE_LAYERS.md`.
- Mise à jour de `doc/docs/architecture/context/20_context.dot`.
- Mise à jour de `doc/docs/architecture/scheduler/10_scheduler.dot`.
- Aucun SVG généré dans ce lot.
- Aucun script de patch fourni.

Les `.dot` modifiés contiennent des commentaires invisibles `ROADMAP_NOTE[phase1_3]` expliquant la raison architecturale du changement.

## Tests

Commandes exécutées sur le workspace Phase 1.2bis + Phase 1.3 :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
```

Résultat :

```text
6 passed
MAIN_OK
```
