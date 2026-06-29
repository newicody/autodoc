# Autodoc / MissiPy — Architecture logicielle Phase 2.6 auditée

Ce document décrit l'état actuel du prototype après audit de cohérence Phase 2.6.

La règle centrale reste inchangée : le Scheduler ne contient pas de logique métier. Il orchestre l'entrée des événements, délègue l'autorisation au `PolicyEngine`, route par `PriorityQueue` puis `Dispatcher`, et expose son activité via une observabilité passive.

## Synthèse courte

État courant : le prototype possède un micro-kernel coopératif testable, un contexte global événementiel, un chemin d'inférence fictif, un registre de backends, une observabilité minimale et une chaîne replay/export isolée.

OpenVINO n'est pas encore intégré. La classe `OpenVINOBackend` existe seulement comme contrat testé avec runtime injecté.

## Layer 0 — Hardware target

Cible connue :

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
- `contracts.replay.ReplayPlan` ;
- `contracts.replay.ReplaySandboxStep` ;
- `contracts.replay.ReplaySandboxResult` ;
- `contracts.replay.ReplayScenario` ;
- `contracts.replay.ReplayScenarioResult` ;
- `contracts.replay.ReplayReport` ;
- `contracts.replay.ReplayReportExport` ;
- `contracts.replay.ReplayReportWriteResult` ;
- `contracts.replay.ReplayBundleWriteResult`.

Décision maintenue : un `Future` ne doit jamais être caché dans `payload`. Il reste dans `Event.request.reply` et ne doit jamais être enregistré dans le journal de replay.

## Layer 3 — Context Fabric

État actuel : collecte événementielle active avec mesure de tick.

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

La collecte touche `ComponentProxy.context()`, pas `Component.context()` directement.

## Layer 4 — Independent Services future

Services prévus mais non branchés :

- Router ;
- SQLite Production ;
- SQLite Maintenance ;
- Qdrant ;
- Cache ;
- Knowledge Manager.

Ces services seront des composants ou handlers pilotés par événements. Ils ne seront pas intégrés dans le Scheduler.

## Layer 5 — Inference

État actuel : chemin fictif actif avec adapter, registry, policy et télémétrie de kernel. La forme du futur backend OpenVINO existe aussi, mais elle utilise encore un runtime injecté de test.

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
  -> BackendRegistry
  -> DummyInferenceBackend
  -> InferenceResult
  -> Request.reply
  -> ComponentProxy
  -> tick().asend(InferenceResult)
```

Un événement observable est aussi publié après succès :

```text
InferenceRequestHandler
  -> EventBus.publish(Event(INFERENCE_RESULT, payload=InferenceResult))
```

Préparation OpenVINO Phase 2.6 :

```text
InferenceAdapter
  -> BackendRegistry
  -> OpenVINOBackend
  -> OpenVINORuntime injecté
  -> InferenceResult
```

Cible future :

```text
OpenVINORuntime réel
  -> Core
  -> CompiledModel
  -> InferRequestPool
  -> InferenceResult
```

OpenVINO ne doit jamais être appelé directement par le Scheduler, le Dispatcher ou le ComponentProxy. En Phase 2.6, `OpenVINOBackend` n'importe pas encore `openvino` : il valide seulement le contrat backend et la frontière d'injection du runtime.

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
- SVG / MIDI.

Tous doivent rester des composants coopératifs exposant `tick()` et `context()`.

## Layer 7 — Validation future

Pipeline prévu :

```text
Compiler
  -> Tests
  -> SemanticValidator
  -> Confidence
  -> Conflict
  -> VersionManager
```

La validation ne doit pas être dans le Scheduler.

## Layer 8 — Learning future

Prévu :

- metrics ;
- ranking ;
- patterns ;
- negative knowledge ;
- MCTS.

Le MCTS produira des propositions, jamais des modifications directes.

## Layer 9 — Observability / Replay

Composants actifs :

- `KernelTelemetry` ;
- `TelemetrySnapshot` ;
- `EventRecorder` ;
- `EventLogSnapshot` ;
- `ReplayReader` ;
- `ReplayPlan` ;
- `ReplaySandbox` ;
- `ReplaySandboxResult` ;
- `ReplayScenario` ;
- `ReplayScenarioRunner` ;
- `ReplayReport` ;
- `ReplayReportExporter` ;
- `ReplayReportExport` ;
- `ReplayReportFileWriter` ;
- `ReplayReportWriteResult` ;
- `ReplayReportBundleWriter` ;
- `ReplayBundleWriteResult`.

Flux complet actuel :

```text
EventBus.publish(Event)
  -> EventRecorder
  -> EventRecord
  -> EventLogSnapshot
  -> ReplayReader
  -> ReplayPlan
  -> ReplaySandbox
  -> ReplaySandboxResult
  -> ReplayScenarioRunner
  -> ReplayReport
  -> ReplayReportExporter
  -> ReplayReportExport
  -> ReplayReportFileWriter
  -> ReplayReportWriteResult
  -> ReplayReportBundleWriter
  -> report.txt / report.json / manifest.json
```

Garanties :

- aucun replay n'est injecté dans le Scheduler vivant ;
- aucun `Future` n'est capturé ;
- aucun payload n'est désérialisé automatiquement ;
- `SHUTDOWN` reste refusé par défaut dans le sandbox ;
- les rapports ne contiennent pas d'horodatage runtime ;
- le texte de rapport est stable et comparable en test ;
- le JSON de rapport est compact, trié et comparable en test ;
- les écritures fichier sont explicites et refusent l'écrasement par défaut ;
- les bundles exposent un manifeste JSON déterministe avec empreintes SHA-256.

## Layer 10 — Test Harness

Commandes de référence :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

État vérifié lors de l'audit Phase 2.6 :

```text
63 passed
main.py exit code: 0
DOT_OK
```

## État stratégique avant OpenVINO

On est maintenant à l'étape juste avant l'intégration réelle d'OpenVINO.

Avant de brancher le runtime réel, il faut décider la stratégie de modèles :

- un modèle d'embedding pour contexte/RAG ;
- un petit modèle de génération pour décisions textuelles ;
- ou plusieurs backends enregistrés dans `BackendRegistry`.

La décision recommandée est de commencer par un backend OpenVINO d'embedding, parce qu'il est plus facile à valider, plus utile pour Qdrant et moins risqué qu'un modèle de génération complet.
