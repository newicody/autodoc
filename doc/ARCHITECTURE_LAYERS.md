# Autodoc / MissiPy — Document de couches logicielles Phase 1

## Objectif de cette phase

Cette phase stabilise le micro-kernel coopératif avant d'ajouter OpenVINO, Qdrant, SQLite, MCTS ou les experts avancés.

Le but immédiat est simple :

```text
Component -> ComponentProxy -> Scheduler -> PriorityQueue -> Dispatcher -> Handler -> Reply
```

Le projet doit pouvoir démarrer, exécuter un composant fictif, traiter un `TICK`, construire un premier contexte global et s'arrêter proprement.

---

## Règle centrale

Aucun composant ne commande directement un autre composant.

Un composant exprime une intention :

```python
yield Event(...)
```

Le Scheduler est le seul interprète de cette intention.

---

## Layer 0 — Hardware

Ce layer représente la machine physique cible.

Cible actuelle :

- Intel i5-11400
- Intel iGPU / OpenVINO futur
- 128 Go DDR4
- ZFS NVMe + RAIDZ2 SATA
- Gentoo Linux

Le Scheduler ne doit jamais dépendre directement du matériel. Le matériel sera exposé plus tard via telemetry, adapters et backends.

---

## Layer 1 — Micro-Kernel

C'est le noyau minimal.

Composants actuels :

- `Launcher`
- `Registry`
- `ComponentProxy`
- `Scheduler`
- `PriorityQueue`
- `Dispatcher`
- `EventBus`
- `LifecycleManager`
- `ContextEngine` Phase 1

Responsabilités :

- démarrer les composants
- recevoir les Events
- ordonnancer par priorité
- dispatcher vers les handlers
- résoudre les réponses via `Request.reply`
- déclencher le contexte périodique
- arrêter proprement

Le kernel ne contient aucune logique métier.

---

## Layer 2 — Contracts

Les contrats forment l'ABI logique du système.

Fichiers actuels :

- `contracts/event.py`
- `contracts/component.py`
- `contracts/context.py`
- `contracts/scheduler.py`
- `contracts/policy.py`
- `contracts/inference.py`

Décisions importantes :

- `Event` est immuable.
- `Event.id` utilise `uuid4`, pas `id(object())`.
- `Future` n'est plus caché dans `payload`.
- Le canal de réponse passe par `Event.request.reply`.
- `payload` reste réservé à la donnée métier.

---

## Layer 3 — Runtime / ComponentProxy

Le proxy isole le composant réel.

Responsabilités :

- démarrer le composant
- émettre `LOAD`
- émettre `START`
- exécuter `tick()`
- intercepter chaque `Event`
- ajouter un `Request(reply=future)`
- attendre le résultat du Scheduler
- renvoyer le résultat au générateur avec `asend()`
- émettre `STOP`
- émettre `ERROR` en cas d'exception
- exposer `context()` au ContextEngine

Aucun composant réel ne doit être enregistré directement dans le Registry.

---

## Layer 4 — Scheduler

Le Scheduler est l'interpréteur central.

Flux actuel :

```text
ComponentProxy
    -> scheduler.emit(event)
    -> PriorityQueue
    -> Scheduler.run()
    -> Dispatcher.dispatch(event)
    -> Handler.handle(event)
    -> Request.reply.set_result(...)
    -> ComponentProxy._dispatch_event(...)
    -> component.tick().asend(result)
```

Le Scheduler connaît :

- Queue
- Dispatcher
- EventBus
- Registry
- ContextEngine

Le Scheduler ne connaît pas :

- OpenVINO
- SQLite
- Qdrant
- MCTS
- les experts métiers
- la validation
- le stockage ZFS

---

## Layer 5 — Context Fabric

Phase actuelle : collecte directe via les proxies.

```text
Clock
    -> ContextEngine.execute_tick()
    -> Registry.all()
    -> ComponentProxy.context()
    -> GlobalContextSnapshot
    -> InferenceContext
```

Mode cible futur :

```text
Clock
    -> GET_CONTEXT_ALL
    -> CONTEXT_REQUEST
    -> ComponentProxy
    -> CONTEXT_REPLY
    -> Collector
    -> Reducer
    -> GlobalContextSnapshot
    -> InferenceContext
    -> DecisionEngine
```

Le snapshot doit rester une image immuable de l'état du système.

---

## Layer 6 — EventBus

L'EventBus est un miroir observable.

Il sert à :

- logger
- métriques
- replay
- dashboard
- observabilité
- synchronisation future

Il ne doit pas être utilisé comme chemin principal de commande.

Chemin de commande :

```text
Scheduler -> PriorityQueue -> Dispatcher -> Handler
```

Chemin d'observation :

```text
Dispatcher -> EventBus -> Observers
```

---

## Layer 7 — Services futurs

Ces services sont prévus mais non intégrés dans le Scheduler :

- Router
- SQLite Production
- SQLite Maintenance
- Qdrant
- Cache
- Knowledge Manager

Ils doivent devenir des composants/services indépendants qui consomment et produisent des Events.

---

## Layer 8 — Inference / OpenVINO futur

OpenVINO ne sera pas le cerveau du système.

OpenVINO sera un backend local derrière un adapter :

```text
InferenceRequest
    -> InferenceAdapter
    -> OpenVINOBackend
    -> InferenceResult
    -> Event
```

Phase 1 ajoute seulement `contracts/inference.py` pour anticiper l'intégration.

---

## Layer 9 — Experts

Les experts sont des composants ordinaires.

Ils devront tous respecter :

```python
tick()
context()
```

Phase actuelle :

- `DummyExpert`

Experts futurs :

- Python
- C
- ASM
- KiCad
- FreeCAD
- Web
- SVG/MIDI
- MetaExpert

---

## Layer 10 — Validation future

La validation sera un pipeline indépendant :

```text
Compiler -> Tests -> SemanticValidator -> Confidence -> Conflict -> VersionManager
```

Le Scheduler ne validera jamais directement du code métier.

---

## Layer 11 — Learning / MCTS futur

Le MCTS ne commande pas le système.

Il produit des propositions :

```text
MCTSProposalEvent -> PolicyEngine -> Scheduler
```

Le learning doit consommer métriques, erreurs, succès, patterns et connaissances négatives.

---

## Layer 12 — Observability

Observability écoute l'EventBus.

Composants futurs :

- Logger
- Metrics
- Replay
- Dashboard
- Watchdog
- Tracer

---

## État Phase 1 livré

Corrections appliquées dans cette proposition :

1. Shebang corrigé dans `main.py`.
2. `Event.id` fiable avec `uuid4`.
3. Ajout de `Request`.
4. Plus de `Future` caché dans `payload`.
5. `Registry` passé au Scheduler.
6. `ContextEngine` ne dépend plus de `scheduler.registry` implicite.
7. `Launcher` démarre les `ComponentProxy`.
8. `ComponentProxy` attend une réponse avec timeout.
9. `Dispatcher` résout automatiquement les replies.
10. Handler `TICK` ajouté.
11. `DummyExpert.tick()` est un vrai générateur asynchrone.
12. Arrêt propre après exécution du DummyExpert en mode Phase 1.
13. `contracts/inference.py` ajouté pour anticiper OpenVINO.
14. DOT mis à jour pour refléter la réalité Phase 1 et les extensions futures.

---

## Commandes de test

Depuis la racine du dépôt après application :

```bash
python3 src/main.py
```

Résultat attendu :

```text
[Lifecycle] LOAD: DummyExpert -> scheduler payload=None
[Lifecycle] START: DummyExpert -> scheduler payload=None
[Tick] DummyExpert: 'hello'
[Lifecycle] STOP: DummyExpert -> scheduler payload=None
```

Compilation :

```bash
python3 -m compileall -q src
```

Génération des graphes :

```bash
cd doc
make
```
