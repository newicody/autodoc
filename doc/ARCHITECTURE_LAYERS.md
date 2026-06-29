# Autodoc / MissiPy — Architecture logicielle Phase 3.2

Ce document décrit l'état actuel du prototype après ajout du profil embedding OpenVINO configurable en Phase 3.2.

La règle centrale reste inchangée : le Scheduler ne contient pas de logique métier. Il orchestre l'entrée des événements, délègue l'autorisation au `PolicyEngine`, route par `PriorityQueue` puis `Dispatcher`, et expose son activité via une observabilité passive.

## Synthèse courte

État courant : le prototype possède un micro-kernel coopératif testable, un contexte global événementiel, un chemin d'inférence fictif, un registre de backends, une observabilité minimale, une chaîne replay/export isolée, un runtime OpenVINO optionnel, un registre déclaratif de profils modèles et une factory qui transforme explicitement un profil en backend enregistrable, et une configuration spécialisée pour déclarer un profil `openvino.embedding` sans modèle imposé.

OpenVINO est intégré sous forme de runtime réel optionnel isolé dans `src/inference/openvino_runtime.py`. La Phase 3.0 ajoute `OpenVINOModelProfileRegistry` pour décrire les modèles possibles sans les charger. La Phase 3.1 ajoute `OpenVINOBackendFactory` pour construire et enregistrer explicitement un backend depuis un profil sélectionné. La Phase 3.2 ajoute `OpenVINOEmbeddingProfileConfig` pour décrire un modèle d'embedding local configurable sans tokenizer ni chemin en dur.

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

Préparation OpenVINO Phase 3.1 :

```text
OpenVINOModelProfileRegistry
  -> OpenVINOModelProfile
  -> OpenVINOEmbeddingProfileConfig optionnel
  -> OpenVINOBackendFactory
  -> OpenVINOBackendConfig
  -> OpenVINOBackend
  -> BackendRegistry.register()
  -> RealOpenVINORuntime optionnel
  -> Core / CompiledModel
  -> InferenceResult
```

Le registre de profils ne remplace pas `BackendRegistry` : il décrit les modèles possibles. La factory est le pont explicite entre les deux. `BackendRegistry` contient seulement les backends exécutables réellement enregistrés.

État actuel du runtime réel :

```text
RealOpenVINORuntime
  -> import openvino isolé
  -> ov.Core()
  -> core.read_model(model_path)
  -> core.compile_model(model, device)
  -> compiled_model(inputs)
  -> InferenceResult
```

OpenVINO ne doit jamais être appelé directement par le Scheduler, le Dispatcher ou le ComponentProxy. `OpenVINOBackend` n'importe toujours pas `openvino` : seul `RealOpenVINORuntime` est autorisé à le faire.

Limite volontaire : aucun tokenizer et aucun modèle local ne sont encore intégrés. Le choix est déclaratif via profils `embedding`, `generation` ou `raw`, puis activé explicitement par la factory. La Phase 3.2 fournit seulement un format configurable pour un profil embedding local. Le runtime réel attend toujours des entrées brutes dans `InferenceRequest.context["inputs"]` ou `InferenceRequest.metadata["inputs"]`.

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

État vérifié après Phase 3.2 :

```text
91 passed
main.py exit code: 0
DOT_OK
```

## État stratégique OpenVINO après Phase 3.2

OpenVINO réel est techniquement isolé, mais le choix du modèle reste volontairement séparé.

Les Phases 3.0 à 3.2 permettent maintenant de décrire :

- un profil `openvino.embedding` pour contexte/RAG ;
- un profil `openvino.generation` pour génération de texte ;
- un profil `openvino.raw` pour tests bas niveau.

La décision recommandée reste de commencer par un profil embedding, parce qu'il est plus facile à valider, plus utile pour Qdrant et moins risqué qu'un modèle de génération complet.

La prochaine étape fonctionnelle logique sera de relier cette configuration à un petit flux de lancement contrôlé, puis seulement ensuite d'ajouter le pré-traitement spécifique au type de modèle.


## Phase 2.8 rule-audit correction

`KernelTelemetry` is now kernel instrumentation and lives in `src/kernel/telemetry.py`.
The passive observability layer still owns recorder/replay/report/export/bundle logic, but it no longer owns the object used directly by the Scheduler.
