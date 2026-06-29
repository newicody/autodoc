# Autodoc / MissiPy — Architecture logicielle Phase 1.3

Ce document décrit l'état de développement après extraction du pipeline de contexte dans `src/context/`.

## Objectif Phase 1.3

La Phase 1.3 verrouille une règle importante : le `ContextEngine` reste une brique fondamentale du noyau, mais les détails de collecte, réduction et construction d'`InferenceContext` ne sont plus dans le scheduler.

Le système garantit maintenant :

- `Event` immuable avec identifiant fiable ;
- `Request.reply` explicite, séparé du `payload` ;
- `Dispatcher` non bloquant même sans handler ;
- `ComponentProxy` stateful et obligatoire ;
- `ContextEngine` composé ;
- `ContextCollector` événementiel ;
- `ContextReducer` dédié ;
- `InferenceContextBuilder` dédié ;
- `ContextRequestHandler` séparé du lifecycle ;
- suite `pytest` minimale couvrant scheduler, proxy, dispatcher, queue et contexte.

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

## Layer 1 — Micro-Kernel

Composants actifs :

- `Launcher` ;
- `Scheduler` ;
- `PriorityQueue` ;
- `Dispatcher` ;
- `EventBus` ;
- `Registry` ;
- `LifecycleManager` ;
- `ComponentProxy`.

Flux runtime :

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

Décision :

```text
Future ne doit jamais être caché dans payload.
```

Il doit rester dans :

```python
Event.request.reply
```

---

## Layer 3 — Context Fabric Phase 1.3

Le fast path `Registry -> proxy.context()` n'est plus le chemin principal du `ContextEngine`.

Flux actuel :

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

Le seul endroit qui touche `ComponentProxy.context()` est `ContextRequestHandler`.

Le Scheduler déclenche le tick de contexte, mais ne connaît pas la logique de collecte, réduction ou projection.

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

## Layer 10 — Test Harness

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
- ContextEngine produit un snapshot via chemin événementiel ;
- CONTEXT_REPLY observable sur EventBus.

---

## Prochaine étape logique

Phase 1.4 : introduire un `PolicyEngine` minimal sans logique métier.

Objectif : préparer les futures décisions de budget, priorité, sécurité et autorisation sans coupler le Scheduler aux services, à OpenVINO ou aux experts.
