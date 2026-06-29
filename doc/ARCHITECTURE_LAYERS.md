# Autodoc / MissiPy — Architecture logicielle Phase 1.6

Ce document décrit l'état de développement après introduction de `PolicyEngine`.

La règle reste inchangée : le Scheduler ne contient pas de logique métier. Il orchestre, mais délègue maintenant explicitement l'autorisation des événements à une politique kernel minimale.

## Objectif Phase 1.6

La Phase 1.6 ajoute une barrière déterministe avant l'entrée en `PriorityQueue`.

Objectifs :

- empêcher un composant de demander un `SHUTDOWN` ;
- empêcher des priorités hors budget kernel ;
- empêcher des destinations non autorisées ;
- empêcher une demande d'inférence vers un modèle/backend non autorisé ;
- retourner un refus explicite via `Request.reply` sans bloquer le composant ;
- publier une copie observable `POLICY_DENIED` sur l'`EventBus`.

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
- `PolicyEngine` ;
- `PriorityQueue` ;
- `Dispatcher` ;
- `EventBus` ;
- `Registry` ;
- `LifecycleManager` ;
- `ComponentProxy`.

Flux d'exécution autorisé :

```text
Component.tick()
  -> yield Event
  -> ComponentProxy
  -> Scheduler.emit()
  -> PolicyEngine.decide()
  -> PriorityQueue
  -> Scheduler.run()
  -> Dispatcher.dispatch()
  -> Handler ou default result
  -> Request.reply
  -> ComponentProxy
  -> tick().asend(result)
```

Flux refusé :

```text
Component.tick()
  -> yield Event interdit
  -> ComponentProxy
  -> Scheduler.emit()
  -> PolicyEngine.decide() == denied
  -> EventBus.publish(POLICY_DENIED)
  -> Request.reply = Decision(allowed=False)
  -> ComponentProxy
  -> tick().asend(Decision)
```

Règle importante : `EventBus` reste un miroir d'observation. Le chemin de commande est `Scheduler -> PolicyEngine -> PriorityQueue -> Dispatcher`.

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
- `contracts.inference.InferenceBackend` ;
- `contracts.policy.Decision`.

Décision maintenue : un `Future` ne doit jamais être caché dans `payload`. Il doit rester dans `Event.request.reply`.

## Layer 3 — Context Fabric

État Phase 1.6 : collecte événementielle active.

```text
Scheduler clock
  -> ContextEngine.execute_tick()
  -> ContextCollector
  -> Event(CONTEXT_REQUEST + Request.reply)
  -> Scheduler.emit()
  -> PolicyEngine.decide()
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

## Layer 5 — Inference Phase 1.6

État actuel : chemin fictif actif avec adapter et politique.

```text
Component
  -> yield Event(INFERENCE_REQUEST, payload=InferenceRequest)
  -> ComponentProxy
  -> Scheduler.emit()
  -> PolicyEngine.decide()
  -> PriorityQueue
  -> Dispatcher
  -> InferenceRequestHandler
  -> InferenceAdapter
  -> DummyInferenceBackend
  -> InferenceResult
  -> Request.reply
  -> ComponentProxy
  -> tick().asend(InferenceResult)
```

Si le modèle demandé n'est pas autorisé :

```text
PolicyEngine
  -> Decision(allowed=False, rule="inference.model.denied")
  -> EventBus.publish(POLICY_DENIED)
  -> Request.reply
```

Un événement observable est aussi publié après succès :

```text
InferenceRequestHandler
  -> EventBus.publish(Event(INFERENCE_RESULT, payload=InferenceResult))
```

Cible future :

```text
InferenceAdapter
  -> OpenVINOBackend
  -> CompiledModel
  -> InferRequestPool
  -> InferenceResult
```

OpenVINO ne doit jamais être appelé directement par le Scheduler, le Dispatcher ou le ComponentProxy.

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
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
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
- InferenceAdapter sélectionne un backend enregistré ;
- InferenceAdapter refuse un backend inconnu ;
- publication observable `INFERENCE_RESULT` ;
- roundtrip composant -> inference handler -> adapter -> backend -> composant ;
- PolicyEngine autorise/refuse les événements structuraux ;
- Scheduler publie `POLICY_DENIED` sans queueing ;
- ComponentProxy reçoit une `Decision` explicite lors d'un refus.

## Prochaine étape logique

Phase 1.7 : préparer une télémétrie kernel minimale.

But : observer proprement les décisions de policy, les événements traités, les refus, les latences et les compteurs de queue avant de brancher OpenVINO.
