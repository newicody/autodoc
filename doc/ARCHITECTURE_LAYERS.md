# Autodoc / MissiPy — Architecture logicielle Phase 1.1

Ce document décrit l'état de développement actuel du logiciel après stabilisation du scheduler Phase 1.1.

## Objectif Phase 1.1

La Phase 1.1 verrouille le noyau minimal avant d'intégrer OpenVINO, Qdrant, SQLite, MCTS ou des experts avancés.

Le système doit maintenant garantir :

- un `Event` immuable avec identifiant fiable ;
- un `Request.reply` explicite, séparé du `payload` ;
- un `Dispatcher` qui ne bloque jamais un composant même si aucun handler n'existe ;
- un `ComponentProxy` stateful ;
- un `LifecycleManager` testable ;
- un `ContextEngine` Phase 1.1 encore en fast path, mais documenté ;
- une suite `pytest` minimale couvrant le scheduler, le proxy, le dispatcher, la queue et le context.

---

## Layer 0 — Hardware target

Cible actuelle :

- Intel i5-11400 ;
- iGPU Intel, futur backend OpenVINO ;
- 128 Go DDR4 ;
- ZFS NVMe + RAIDZ2 SATA ;
- Gentoo Linux.

Le Scheduler ne dépend d'aucune ressource matérielle directement.

---

## Layer 1 — Micro-Kernel Phase 1.1

Composants actifs :

- `Launcher` ;
- `Scheduler` ;
- `PriorityQueue` ;
- `Dispatcher` ;
- `EventBus` ;
- `Registry` ;
- `LifecycleManager` ;
- `ComponentProxy`.

Flux actuel :

```text
Component.tick()
    -> yield Event
    -> ComponentProxy
    -> Scheduler.emit()
    -> PriorityQueue
    -> Scheduler.run()
    -> Dispatcher.dispatch()
    -> Handler ou default result
    -> Request.reply
    -> ComponentProxy
    -> tick().asend(result)
```

Règle importante : `EventBus` reste un miroir d'observation. Le chemin de commande est `Scheduler -> PriorityQueue -> Dispatcher`.

---

## Layer 2 — Contracts

Contrats disponibles :

- `contracts.event.Event` ;
- `contracts.event.Request` ;
- `contracts.component.Component` ;
- `contracts.context.GlobalContextSnapshot` ;
- `contracts.context.InferenceContext` ;
- `contracts.lifecycle.ComponentState` ;
- `contracts.inference.InferenceRequest` ;
- `contracts.inference.InferenceResult`.

Décision Phase 1.1 :

```text
Future ne doit jamais être caché dans payload.
```

Il doit rester dans :

```python
Event.request.reply
```

---

## Layer 3 — Context Fabric

État actuel : fast path assumé.

```text
Scheduler clock
    -> ContextEngine.execute_tick()
    -> EventBus.publish(CONTEXT_REQUEST)
    -> Registry.all()
    -> ComponentProxy.context()
    -> Component.context()
    -> GlobalContextSnapshot
    -> InferenceContext
```

Cible future :

```text
CONTEXT_REQUEST
    -> ComponentProxy
    -> CONTEXT_REPLY
    -> Collector
    -> Reducer
    -> GlobalContextSnapshot
    -> InferenceContext
    -> DecisionEngine
```

Le fast path est accepté uniquement parce que la Phase 1.1 teste encore le noyau.

---

## Layer 4 — Independent Services future

Services prévus mais non branchés :

- Router ;
- SQLite Production ;
- SQLite Maintenance ;
- Qdrant ;
- Cache ;
- Knowledge Manager.

Ces services seront des composants ou handlers pilotés par événements. Ils ne seront pas intégrés dans le Scheduler.

---

## Layer 5 — Inference future

État actuel : uniquement les contrats.

Prévu :

```text
InferenceRequest
    -> InferenceAdapter
    -> DummyInferenceBackend
    -> InferenceResult
```

Puis seulement ensuite :

```text
InferenceAdapter
    -> OpenVINOBackend
    -> CompiledModel
    -> InferRequestPool
```

OpenVINO ne doit jamais être appelé directement par le Scheduler.

---

## Layer 6 — Experts

Actuel :

- `DummyExpert`.

Futurs experts :

- Python ;
- C ;
- ASM ;
- KiCad ;
- FreeCAD ;
- Web ;
- SVG ;
- MIDI ;
- Meta Expert.

Chaque expert est un composant coopératif standard.

---

## Layer 7 — Validation future

Prévu :

```text
Compiler
    -> Tests
    -> Semantic Validator
    -> Confidence
    -> Conflict
    -> Version Manager
```

Le LLM ne remplace jamais les validateurs techniques.

---

## Layer 8 — Learning future

Prévu :

- metrics ;
- ranking ;
- patterns ;
- benchmark ;
- negative knowledge ;
- MCTS.

Le MCTS produit des propositions, jamais des actions directes.

---

## Layer 9 — Observability

Prévu :

- logger ;
- metrics ;
- dashboard ;
- replay ;
- tracer ;
- watchdog ;
- recovery.

Observability écoute l'EventBus mais ne commande pas le kernel.

---

## Layer 10 — Test Harness Phase 1.1

Commandes de validation :

```bash
python3 -m compileall -q src tests
pytest -q
cd doc && make -f makefile
```

Couverture actuelle :

- Event ids uniques ;
- Dispatcher sans handler ne bloque pas ;
- PriorityQueue FIFO à priorité égale ;
- ComponentProxy roundtrip `yield/asend` ;
- événement inconnu non bloquant ;
- composant qui plante : ERROR + kernel non bloqué ;
- ContextEngine produit un snapshot.

---

## Prochaine étape logique

Phase 1.2 : rendre le Context Engine pleinement événementiel.

Cela supprimera le fast path :

```python
await proxy.context()
```

au profit de :

```text
CONTEXT_REQUEST -> CONTEXT_REPLY -> Collector -> Reducer
```
