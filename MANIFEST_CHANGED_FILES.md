# Manifest — Phase 1.3 changed files

Ce lot ne contient pas de script de patch et ne contient aucun SVG.

## Fichiers ajoutés

```text
src/context/__init__.py
src/context/builder.py
src/context/collector.py
src/context/engine.py
src/context/handlers.py
src/context/reducer.py
```

## Fichiers modifiés

```text
src/kernel/context_engine.py
src/kernel/lifecycle.py
src/kernel/scheduler.py
src/kernel/launcher.py
src/runtime/component.py
tests/context/test_context_engine.py

doc/ARCHITECTURE_LAYERS.md
doc/CHANGELOG_PHASE1_3.md
doc/docs/architecture/context/20_context.dot
doc/docs/architecture/scheduler/10_scheduler.dot
```

## Raison architecturale

La Phase 1.3 extrait la logique de contexte hors du `kernel/` tout en conservant le `ContextEngine` comme brique fondamentale du micro-kernel.

Le Scheduler déclenche le contexte, mais ne contient pas la logique de collecte, réduction ou construction d'`InferenceContext`.
