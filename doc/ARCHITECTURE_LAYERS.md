# Autodoc / MissiPy — Architecture logicielle Phase 1.4

Ce document décrit l'état de développement après introduction du premier chemin d'inférence fictif.

La règle reste inchangée : le Scheduler ne contient pas d'IA, ne connaît pas OpenVINO et ne manipule pas directement les backends. Il route des événements.

## Objectif Phase 1.4

La Phase 1.4 ajoute un `DummyInferenceBackend` pour valider le contrat d'inférence avant OpenVINO.

Objectifs :

- tester `InferenceRequest` / `InferenceResult` ;
- tester `EventType.INFERENCE_REQUEST` ;
- tester `EventType.INFERENCE_RESULT` observable ;
- vérifier qu'un composant peut recevoir un résultat d'inférence via `Request.reply` ;
- garder OpenVINO hors du Scheduler ;
- préserver `EventBus` comme miroir d'observation.

## Layer 0 — Hardware target

Cible actuelle :

- Intel i5-11400 ;
- iGPU Intel, futur backend OpenVINO ;
- 128 Go DDR4 ;
- ZFS NVMe + RAIDZ2 SATA ;
- Gentoo Linux.

Le Scheduler ne dépend directement d'aucune ressource matérielle.

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

Flux d'exécution :

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

## Layer 2 — Contracts

Contrats disponibles :

- `contracts.event.Event` ;
- `contracts.event.Request` ;
- `contracts.component.Component` ;
- `contracts.context.GlobalContextSnapshot` ;
- `contracts.context.InferenceContext` ;
- `contracts.lifecycle.ComponentState` ;
- `contracts.inference.InferenceRequest` ;
- `contracts.inference.InferenceResult` ;
- `contracts.inference.InferenceBackend`.

Décision maintenue : un `Future` ne doit jamais être caché dans `payload`. Il doit rester dans `Event.request.reply`.

## Layer 3 — Context Fabric

État Phase 1.4 : collecte événementielle active.

```text
Scheduler clock
  -> ContextEngine.execute_tick()
  -> ContextCollector
  -> Event(CONTEXT_REQUEST + Request.reply)
  -> Scheduler.emit()
  -> PriorityQueue
  -> Dispatcher
  -> ContextRequestHandler
  -> ComponentProxy.context()
  -> Request.reply
  -> EventBus.publish(CONTEXT_REPLY)
  -> ContextReducer
  -> GlobalContextSnapshot
  -> InferenceContext
```

La collecte touche encore `ComponentProxy.context()`, pas `Component.context()` directement. Cela respecte l'isolation du noyau.

## Layer 4 — Independent Services future

Services prévus mais non branchés :

- Router ;
- SQLite Production ;
- SQLite Maintenance ;
- Qdrant ;
- Cache ;
- Knowledge Manager.

Ces services seront des composants ou handlers pilotés par événements. Ils ne seront pas intégrés dans le Scheduler.

## Layer 5 — Inference Phase 1.4

État actuel : chemin fictif actif.

```text
Component
  -> yield Event(INFERENCE_REQUEST, payload=InferenceRequest)
  -> ComponentProxy
  -> Scheduler.emit()
  -> PriorityQueue
  -> Dispatcher
  -> InferenceRequestHandler
  -> DummyInferenceBackend
  -> InferenceResult
  -> Request.reply
  -> ComponentProxy
  -> tick().asend(InferenceResult)
```

Un événement observable est aussi publié :

```text
InferenceRequestHandler
  -> EventBus.publish(Event(INFERENCE_RESULT, payload=InferenceResult))
```

Cible future :

```text
InferenceRequestHandler
  -> OpenVINOBackend
  -> CompiledModel
  -> InferRequestPool
  -> InferenceResult
```

OpenVINO ne doit jamais être appelé directement par le Scheduler.

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

## Layer 7 — Validation future

Prévu :

```text
Compiler -> Tests -> Semantic Validator -> Confidence -> Conflict -> Version Manager
```

Le LLM ne remplace jamais les validateurs techniques.

## Layer 8 — Learning future

Prévu :

- metrics ;
- ranking ;
- patterns ;
- benchmark ;
- negative knowledge ;
- MCTS.

Le MCTS produit des propositions, jamais des actions directes.

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

## Layer 10 — Test Harness

Commandes de validation :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
cd doc && make -f makefile
```

Couverture actuelle :

- ids d'événements uniques ;
- Dispatcher sans handler non bloquant ;
- PriorityQueue FIFO à priorité égale ;
- ComponentProxy roundtrip `yield/asend` ;
- événement inconnu non bloquant ;
- composant qui plante : `ERROR` + kernel non bloqué ;
- ContextEngine collecte via événements ;
- DummyInferenceBackend déterministe ;
- publication observable `INFERENCE_RESULT` ;
- roundtrip composant -> inference handler -> backend -> composant.

## Prochaine étape logique

Phase 1.5 : introduire un premier `PolicyEngine` minimal ou un `InferenceAdapter` plus explicite.

Ordre conseillé :

1. verrouiller `InferenceRequestHandler` ;
2. ajouter `InferenceAdapter` si le backend doit devenir interchangeable ;
3. seulement ensuite brancher `OpenVINOBackend` ;
4. garder `DummyInferenceBackend` comme backend de test permanent.
