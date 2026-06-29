# Autodoc / MissiPy

`autodoc` est le prototype du micro-kernel coopératif IA MissiPy.

L'objectif n'est pas de construire une application Python monolithique, mais un noyau d'orchestration modulaire, observable, déterministe et rejouable.

## État courant

État de référence : **Phase 2.9 OpenVINO runtime isolé**.

Le prototype possède actuellement :

- un `Scheduler` coopératif ;
- une `PriorityQueue` comme chemin de commande ;
- un `Dispatcher` ;
- un `EventBus` passif, réservé à l'observation ;
- un `ComponentProxy` obligatoire entre le noyau et les composants réels ;
- un `ContextEngine` événementiel ;
- un `PolicyEngine` minimal ;
- une télémétrie kernel minimale (`kernel.telemetry`) ;
- une chaîne replay hors Scheduler vivant ;
- un chemin d'inférence fictif ;
- un `BackendRegistry` ;
- un contrat `OpenVINOBackend` ;
- un `RealOpenVINORuntime` optionnel, isolé dans `src/inference/openvino_runtime.py`, sans modèle imposé.

OpenVINO est branché uniquement comme runtime générique à entrées brutes. Le choix du ou des modèles reste explicite : embedding, génération ou multi-backend ne sont pas encore décidés.

## Règle d'architecture

Le Scheduler ne contient pas de logique métier.

Le chemin d'exécution est :

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

Le chemin d'observation est séparé :

```text
EventBus.publish(Event)
  -> telemetry / recorder / replay artifacts
```

## Commandes de validation

Depuis la racine du dépôt :

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Documentation

- `code_rule.md` : philosophie et règles de codage.
- `doc/ARCHITECTURE_LAYERS.md` : couches logicielles actuelles.
- `doc/PROJECT_REVIEW_PHASE2_6.md` : audit du modèle actuel.
- `doc/OPENVINO_MODEL_STRATEGY.md` : stratégie proposée avant choix du ou des modèles OpenVINO.
- `doc/docs/architecture/*.dot` : roadmap DOT navigable ; les SVG sont générés par le makefile.

## Développement

Les fichiers `.svg` ne sont pas édités à la main. Les graphes sources sont les `.dot`.

Les fichiers de cache Python (`__pycache__`, `.pyc`, `.pytest_cache`) ne doivent pas être versionnés.

## Rule audit

Before integrating real OpenVINO runtime code, the repository includes code-rule guard tests:

```bash
PYTHONPATH=src pytest -q tests/rules
```

These tests enforce the current interpretation of `code_rule.md`: stdlib-first imports, frozen contract dataclasses, Scheduler isolation from backend/domain layers, and no direct OpenVINO import outside the explicit runtime phase.
