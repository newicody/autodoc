# Autodoc / MissiPy — Architecture logicielle Phase 3.14

Ce document décrit l'état actuel du prototype après ajout du corpus local depuis sources TXT/Markdown et du rapport de recherche E5 avec contexte source en Phase 3.14.

La règle centrale reste inchangée : le Scheduler ne contient pas de logique métier. Il orchestre l'entrée des événements, délègue l'autorisation au `PolicyEngine`, route par `PriorityQueue` puis `Dispatcher`, et expose son activité via une observabilité passive.

## Synthèse courte

État courant : le prototype possède un micro-kernel coopératif testable, un contexte global événementiel, un chemin d'inférence fictif, un registre de backends, une observabilité minimale, une chaîne replay/export isolée, un runtime OpenVINO optionnel, un registre déclaratif de profils modèles, une factory de backends, une chaîne embedding E5 locale validée avec OpenVINO, un contrat query/passage, un mini-ranker local, un corpus local persistant depuis passages ou sources TXT/Markdown, et un rapport de recherche avec score, fichier, lignes et extrait avant Qdrant.

OpenVINO est intégré sous forme de runtime réel optionnel isolé dans `src/inference/openvino_runtime.py`. La Phase 3.0 ajoute `OpenVINOModelProfileRegistry` pour décrire les modèles possibles sans les charger. La Phase 3.1 ajoute `OpenVINOBackendFactory` pour construire et enregistrer explicitement un backend depuis un profil sélectionné. La Phase 3.2 ajoute `OpenVINOEmbeddingProfileConfig` pour décrire un modèle d'embedding local configurable sans tokenizer ni chemin en dur. La Phase 3.3 ajoute `OpenVINOEmbeddingRawInputs` et `OpenVINOEmbeddingOutputAdapter` pour séparer tokens, inférence brute et vecteur final. La Phase 3.4 ajoute `TokenizerConfig`, `TokenizationRequest`, `TokenizationResult`, `TextTokenizer` et `TokenizerRegistry` pour représenter texte -> tokens sans choisir Hugging Face, SentencePiece ou un tokenizer maison. La Phase 3.5 ajoute `OpenVINOEmbeddingPipeline` pour assembler ce contrat avec les inputs bruts, `InferenceAdapter` et `OpenVINOEmbeddingOutputAdapter`. La Phase 3.6 ajoute `DeterministicTokenizer`, un tokenizer pure stdlib réservé au test du pipeline, sans vocabulaire réel et sans compatibilité modèle revendiquée. Les Phases 3.7 à 3.11 valident ensuite `multilingual-e5-small` local avec OpenVINO, ajoutent la factory E5, la CLI embedding, le contrat `query:` / `passage:` et la CLI de ranking local.

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
  -> DeterministicTokenizer de test optionnel
  -> TokenizationResult optionnel
  -> OpenVINOEmbeddingRawInputs optionnel
  -> OpenVINOBackendFactory
  -> OpenVINOBackendConfig
  -> OpenVINOBackend
  -> BackendRegistry.register()
  -> RealOpenVINORuntime optionnel
  -> Core / CompiledModel
  -> InferenceResult.metadata["raw_outputs"]
  -> OpenVINOEmbeddingOutputAdapter
  -> OpenVINOEmbeddingVector
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

Limite volontaire : aucun tokenizer concret et aucun modèle local ne sont encore intégrés. Le choix est déclaratif via profils `embedding`, `generation` ou `raw`, puis activé explicitement par la factory. La Phase 3.2 fournit un format configurable pour un profil embedding local. La Phase 3.3 fournit le contrat raw pour transporter `input_ids`, `attention_mask`, `token_type_ids` optionnel et pour transformer une sortie brute en `OpenVINOEmbeddingVector`. La Phase 3.4 fournit le contrat tokenizer abstrait qui peut produire ces matrices sans imposer l’implémentation concrète. Le runtime réel attend toujours des entrées brutes dans `InferenceRequest.context["inputs"]` ou `InferenceRequest.metadata["inputs"]`. La Phase 3.5 exploite `InferenceResult.metadata["raw_outputs"]` pour post-traiter un vecteur embedding en chemin direct, hors Scheduler.


### Phase 3.6 — Tokenizer déterministe de test

La Phase 3.6 ajoute un tokenizer concret minimal mais volontairement limité :

```text
TokenizationRequest
  -> DeterministicTokenizer
  -> TokenizationResult
  -> OpenVINOEmbeddingRawInputs
  -> OpenVINOEmbeddingPipeline
```

Ce tokenizer sert à tester le pipeline sans dépendance externe. Il utilise SHA-256 pour produire des ids stables et ne doit pas être confondu avec le tokenizer réel d'un modèle BGE, E5, MiniLM ou Qwen. Le vrai tokenizer viendra après validation de l'installation OpenVINO et du modèle local choisi.


### Phase 3.14 — Rapport de résultats E5

La Phase 3.14 ajoute une projection lisible des résultats du corpus local :

```text
E5CorpusSearchResults
  -> E5SearchReport
  -> score + source_path + start_line/end_line + excerpt
```

Cette couche ne relit pas encore les fichiers sources sur disque. Elle exploite les métadonnées persistées dans `corpus.json` depuis la Phase 3.13. Elle prépare l'affichage d'un résultat exploitable avant Qdrant et avant un frontend.

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

État vérifié après Phase 3.9 :

```text
133 passed, 1 skipped
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

## Phase 3.8 — Factory de pipeline E5 local

La couche `inference.e5_pipeline` assemble explicitement le premier modèle réel validé localement : profil `multilingual-e5-small`, tokenizer local Transformers, runtime OpenVINO réel et pipeline embedding.

Cette factory ne change pas le Scheduler. Elle devient le point d'entrée contrôlé pour activer le modèle E5 dans un launcher ou un futur composant de configuration.

```text
MultilingualE5SmallPipelineConfig
  -> MultilingualE5SmallPipelineFactory
  -> MultilingualE5SmallPipelineBundle
      -> OpenVINOEmbeddingPipeline
      -> OpenVINOModelProfileRegistry
      -> TokenizerRegistry
      -> BackendRegistry
      -> MultilingualE5SmallPipelineBuildSummary
```

Le résumé de construction reste immuable et ne transporte aucun objet vivant. Le bundle, lui, est explicitement un objet d'exécution.


## Phase 3.9 — CLI de développement E5 local

La couche `inference.e5_cli` expose le pipeline E5 validé localement sous forme de commande de développement. Elle reste hors Scheduler : elle construit un bundle E5 explicite, exécute `embed_text()` et imprime un diagnostic texte ou JSON.

```text
tools/embed_e5.py
  -> inference.e5_cli
  -> MultilingualE5SmallPipelineFactory
  -> OpenVINOEmbeddingPipeline
  -> OpenVINOEmbeddingVector
  -> sortie text/json
```

Cette phase ne transforme pas le pipeline en composant kernel. Elle sert uniquement à tester rapidement le modèle local depuis le terminal et à préparer la future étape `query:` / `passage:` avant indexation vectorielle.

## Phase 3.10 — Contrat query/passage E5

La couche `inference.e5_text` rend explicite la distinction entraînée par E5 : `query:` pour le texte qui cherche, `passage:` pour le texte qui peut être retrouvé.

```text
E5Text.query(...)
  -> "query: ..."

E5Text.passage(...)
  -> "passage: ..."
```

La couche `inference.e5_ranker` ajoute un mini-ranker local avant Qdrant :

```text
query
  -> embedding query
passages
  -> embeddings passages
  -> dot_product
  -> E5RankedResults
```

Ce ranker ne remplace pas Qdrant. Il sert à valider le comportement sémantique du modèle local sur quelques passages avant d'introduire persistance, index vectoriel et batch.


## Phase 3.11 — CLI de ranking local E5

La couche `inference.e5_rank_cli` expose le mini-ranker local sous forme de commande de développement. Elle reste hors Scheduler et hors Qdrant : elle construit explicitement le pipeline E5 local, encode une query, encode les passages fournis, puis classe les passages par produit scalaire.

```text
tools/rank_e5.py
  -> inference.e5_rank_cli
  -> MultilingualE5SmallPipelineFactory
  -> E5LocalRanker
  -> OpenVINOEmbeddingPipeline
  -> E5RankedResults
  -> sortie text/json
```

Cette étape valide le comportement sémantique sur un mini-corpus avant d'ajouter un stockage vectoriel. Elle ne met pas encore les embeddings en cache et ne crée pas d'index persistant.


## Phase 3.12 — Corpus local E5

La couche inference contient maintenant un corpus local persistant pour les passages E5.

```text
OpenVINOEmbeddingPipeline
  -> E5CorpusBuilder
  -> E5CorpusIndex
  -> E5CorpusJsonStore
  -> E5CorpusSearcher
```

Cette couche est volontairement hors Scheduler. Elle permet de valider la logique `query -> corpus local -> scores` avant l'introduction d'un vector store externe comme Qdrant.


## Phase 3.13 — Sources locales TXT/Markdown

La couche inference dispose maintenant d’un chargeur de sources locales (`e5_sources.py`) capable de découvrir des fichiers `.md`, `.markdown` et `.txt`, de les découper en chunks de passages et de produire des `E5CorpusDocument` enrichis en métadonnées.

Cette brique reste hors Scheduler et hors Qdrant : elle prépare le futur Knowledge Manager en validant d’abord la chaîne locale fichier -> chunk -> embedding -> corpus JSON.

## Phase 3.15 — Corpus E5 incrémental

Le corpus local E5 peut maintenant être reconstruit en réutilisant les embeddings inchangés.

Flux :

```text
sources TXT/Markdown
  -> chunks déterministes
  -> document_hash
  -> ancien E5CorpusIndex optionnel
  -> E5IncrementalCorpusBuilder
  -> reuse ou embed
  -> nouveau E5CorpusIndex
```

La règle d'invalidation est déterministe : elle ne dépend pas des timestamps mais de l'identifiant du document et de son texte préfixé E5. Cette couche reste hors Scheduler et prépare les futurs `upsert/delete` Qdrant.
