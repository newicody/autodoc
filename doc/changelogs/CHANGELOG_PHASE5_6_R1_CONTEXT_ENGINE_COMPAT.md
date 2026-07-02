# Changelog — Phase 5.6-r1 — ContextEngine compatibility

## Objectif

Corriger la régression introduite en 5.6 : `src/context/engine.py` avait remplacé le constructeur historique du `ContextEngine` par un constructeur limité à un `InferenceContext` optionnel.

Le `Scheduler` construit toujours :

```python
ContextEngine(registry, self, event_bus)
```

La 5.6-r1 restaure donc cette compatibilité sans déplacer l'intake E5 dans le Scheduler.

## Changements

- `ContextEngine.__init__()` accepte de nouveau le mode historique :
  - `registry` ;
  - `scheduler` ;
  - `event_bus`.
- `ContextEngine(_base_inference_context)` reste compatible avec les tests 5.6.
- `execute_tick()` est restauré comme entrée de tick contexte.
- L'intake E5 reste explicite :
  - `attach_e5_artifact_dir(...)` ;
  - `attach_e5_runtime_context(...)`.

## Frontières maintenues

```text
pas d'autoload E5
pas de Scheduler vivant déclenché par E5
pas de daemon
pas de réseau
pas d'API GitHub
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.6-r1 restaure une compatibilité de constructeur ContextEngine sans nouvelle règle de programmation.
```
