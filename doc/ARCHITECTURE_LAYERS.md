# Autodoc / MissiPy — Architecture logicielle Phase 1.9

Ce document décrit l'état de développement après introduction du `ReplayReader` minimal.

La règle centrale reste inchangée : le Scheduler ne contient pas de logique métier. Il orchestre, délègue l'autorisation au `PolicyEngine`, route via la `PriorityQueue` et le `Dispatcher`, puis alimente une instrumentation passive.

## Objectif Phase 1.9

La Phase 1.9 ajoute la lecture contrôlée du journal d'événements.

Objectifs :

- conserver `EventRecorder` comme observateur passif ;
- lire un `EventLogSnapshot` sans toucher au Scheduler ;
- filtrer les événements par type, source ou destination ;
- produire un `ReplayPlan` immuable ;
- ne pas reconstruire de `Request.reply` ;
- ne pas désérialiser automatiquement le payload ;
- préparer le replay déterministe futur sans le brancher au chemin d'exécution.

Flux Phase 1.9 :

```text
EventBus.publish(Event)
  -> EventRecorder
  -> EventRecord immuable
  -> EventLogSnapshot
  -> ReplayReader
  -> ReplayPlan contrôlé
```

`ReplayReader` ne commande rien. Il ne publie rien. Il ne connaît pas le Scheduler.

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
- `ComponentProxy` ;
- `KernelTelemetry`.

Flux d'exécution autorisé :

```text
Component.tick()
  -> yield Event
  -> ComponentProxy
  -> Scheduler.emit()
  -> PolicyEngine.decide()
  -> PriorityQueue
  -> KernelTelemetry.record_enqueue()
  -> Scheduler.run()
  -> KernelTelemetry.record_dequeue()
  -> Dispatcher.dispatch()
  -> Handler ou default result
  -> KernelTelemetry.record_dispatch_success()
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
  -> KernelTelemetry.record_policy_denied()
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
- `contracts.policy.Decision` ;
- `contracts.telemetry.TelemetrySnapshot` ;
- `contracts.replay.EventRecord` ;
- `contracts.replay.EventLogSnapshot` ;
- `contracts.replay.ReplayEvent` ;
- `contracts.replay.ReplayPlan`.

Décision maintenue : un `Future` ne doit jamais être caché dans `payload`. Il doit rester dans `Event.request.reply` et ne doit jamais être enregistré dans le journal de replay.

## Layer 3 — Context Fabric

État Phase 1.9 : collecte événementielle active avec mesure de tick.

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
  -> KernelTelemetry.record_context_tick()
```

La collecte touche `ComponentProxy.context()`, pas `Component.context()` directement. Cela respecte l'isolation du noyau.

## Layer 4 — Independent Services future

Services prévus mais non branchés :

- Router ;
- SQLite Production ;
- SQLite Maintenance ;
- Qdrant ;
- Cache ;
- Knowledge Manager.

Ces services seront des composants ou handlers pilotés par événements. Ils ne seront pas intégrés dans le Scheduler.

## Layer 5 — Inference Phase 1.9

État actuel : chemin fictif actif avec adapter, policy et télémétrie de kernel.

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
  -> KernelTelemetry.record_policy_denied()
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

## Layer 9 — Observability Phase 1.9

Actuel :

- `KernelTelemetry` ;
- `TelemetrySnapshot` ;
- `EventRecorder` ;
- `EventLogSnapshot` ;
- `ReplayReader` ;
- `ReplayPlan`.

Prévu :

- logger ;
- metrics ;
- dashboard ;
- replay effectif ;
- tracer ;
- watchdog ;
- recovery.

Observability écoute l'EventBus ou lit des snapshots. Elle ne commande pas le kernel.

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
- ComponentProxy reçoit une `Decision` explicite lors d'un refus ;
- KernelTelemetry compte enqueue/dequeue/dispatch ;
- KernelTelemetry compte les refus policy sans queueing ;
- TelemetrySnapshot expose des moyennes immuables ;
- EventRecorder capture passivement les événements observés ;
- EventLogSnapshot reste immuable ;
- ReplayReader filtre par type/source/destination ;
- ReplayReader produit un ReplayPlan contrôlé et immuable.

## Prochaine étape logique

Phase 2.0 : ajouter un moteur de replay contrôlé qui peut prendre un `ReplayPlan` et le rejouer dans un environnement isolé, sans affecter le Scheduler de production.

Le replay effectif ne doit pas réinjecter directement les événements dans le kernel courant. Il doit passer par une instance de test/simulation ou par une API explicite de replay.
