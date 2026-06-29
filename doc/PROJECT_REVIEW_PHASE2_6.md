# Autodoc / MissiPy — Revue d'architecture Phase 2.6

## Résumé

Le modèle de départ était un micro-kernel coopératif piloté par événements. Ce modèle est toujours la base, mais il a évolué vers une architecture plus précise : la chaîne de commande, la chaîne d'observation, la chaîne de contexte, la chaîne d'inférence et la chaîne replay sont maintenant séparées.

L'état actuel est cohérent avec les préceptes de départ : le Scheduler reste petit, les composants ne s'appellent pas directement, les intentions passent par `Event`, et les résultats reviennent par `Request.reply`.

## Modèle de départ

Le modèle initial disait :

```text
Component
  -> yield Event(...)
  -> Scheduler
  -> système
```

C'était correct comme vision, mais trop compact.

## Modèle actuel

Le modèle actuel est plus explicite :

```text
Component.tick()
  -> yield Event(...)
  -> ComponentProxy
  -> Scheduler.emit()
  -> PolicyEngine.decide()
  -> PriorityQueue
  -> Scheduler.run()
  -> Dispatcher
  -> Handler
  -> Request.reply
  -> ComponentProxy
  -> tick().asend(result)
```

En parallèle :

```text
EventBus.publish(Event)
  -> KernelTelemetry
  -> EventRecorder
  -> ReplayReader / ReplaySandbox / ReplayReport
```

La séparation importante est donc :

- `PriorityQueue` = chemin de commande ;
- `EventBus` = chemin d'observation ;
- `PolicyEngine` = barrière explicite ;
- `ComponentProxy` = membrane entre noyau et composants ;
- `BackendRegistry` = inventaire explicite des backends d'inférence ;
- `Replay` = banc d'audit hors Scheduler vivant.

## Points positifs

### 1. Le Scheduler reste protégé

Le Scheduler ne connaît pas OpenVINO, Qdrant, SQLite ou les experts métier. C'est essentiel pour conserver un noyau stable.

### 2. Les contrats sont devenus solides

`Event`, `Request`, `InferenceRequest`, `InferenceResult`, `Decision`, `GlobalContextSnapshot` et les contrats replay sont immuables ou manipulés comme des valeurs stables.

### 3. L'inférence est découplée

Le chemin actuel :

```text
InferenceRequestHandler
  -> InferenceAdapter
  -> BackendRegistry
  -> InferenceBackend
```

permet d'ajouter `OpenVINOBackend` sans modifier le Scheduler.

### 4. Le replay est utile dès maintenant

Le replay permet de conserver la trace observable d'un flux, de produire un plan, de le rejouer dans un sandbox et de générer un rapport déterministe.

Cela servira à tester les futures modifications de policy, d'inférence ou de routing.

### 5. Les graphes DOT jouent leur rôle de roadmap

Les DOT ne sont pas seulement de la documentation : ils servent à visualiser le niveau courant et les zooms possibles.

## Points négatifs / limites actuelles

### 1. Le prototype reste encore en mémoire

Il n'y a pas encore de stockage durable contrôlé pour les événements, contextes, snapshots ou artefacts hors export replay.

### 2. La Policy est encore très simple

Le `PolicyEngine` protège déjà les événements de base, mais il ne connaît pas encore les budgets CPU/GPU, la mémoire, le coût d'inférence, les quotas ou les profils de composants.

### 3. Le ContextEngine ne pilote pas encore vraiment les décisions

Le contexte est collecté et transformé, mais il n'influence pas encore fortement le scheduling, les budgets ou la sélection de backends.

### 4. OpenVINO est préparé, pas intégré

Le contrat est bon, mais il n'y a pas encore de runtime réel, pas de modèle chargé, pas de tokenizer, pas de normalisation des entrées/sorties.

### 5. Le choix des modèles n'est pas défini

On ne sait pas encore s'il faut brancher un embedding model, un text-generation model, ou plusieurs backends. Cela doit être décidé avant d'importer OpenVINO.

### 6. Les experts sont encore fictifs

`DummyExpert` valide le protocole, mais pas encore le modèle multi-experts réel.

## Axes d'amélioration

### Court terme

1. Décider la stratégie OpenVINO : embedding d'abord, génération ensuite, ou multi-backend.
2. Brancher un runtime OpenVINO réel derrière `OpenVINORuntime`.
3. Ajouter un test d'intégration désactivable si OpenVINO n'est pas installé.
4. Exposer le snapshot du `BackendRegistry` dans le contexte global.
5. Ajouter une policy explicite pour autoriser `openvino`.

### Moyen terme

1. Ajouter un `ModelRegistry` séparé du `BackendRegistry`.
2. Ajouter `SQLite Maintenance` pour conserver replay, métriques et erreurs.
3. Ajouter `Qdrant` pour mémoire vectorielle.
4. Ajouter un expert Python réel.
5. Ajouter un routeur de tâches vers experts.

### Long terme

1. Ajouter MCTS comme générateur de propositions, jamais comme contrôleur direct.
2. Ajouter apprentissage par benchmark et negative knowledge.
3. Ajouter supervision resource-aware CPU/iGPU/RAM.
4. Ajouter mode replay comparatif entre deux versions du kernel.
5. Ajouter interface de visualisation dynamique basée sur DOT + télémétrie.

## Recommandation stratégique

Ne pas brancher directement un modèle de génération en premier.

Commencer par un modèle d'embedding OpenVINO est plus sûr :

- entrées/sorties plus simples ;
- validation plus facile ;
- utile immédiatement pour Qdrant ;
- coût plus prévisible ;
- moins de risques de bloquer le Scheduler.

Ensuite seulement brancher un petit modèle de génération.
