# Manifest — Phase 2.2

## Objectif

Ajouter un export déterministe de `ReplayReport`, en texte et JSON standard library, sans brancher le replay au Scheduler vivant.

## Fichiers modifiés

```text
src/contracts/replay.py
src/observability/__init__.py
src/observability/replay_exporter.py
tests/observability/test_replay_exporter.py

doc/ARCHITECTURE_LAYERS.md
doc/CHANGELOG_PHASE2_2.md

doc/docs/architecture/00_global.dot
doc/docs/architecture/observability/70_observability.dot
doc/docs/architecture/tests/80_tests.dot
```

## Contraintes respectées

- Aucun script de patch.
- Aucun SVG.
- Aucun accès au Scheduler.
- Aucun `Event` vivant dans l'export.
- Aucun `Future` capturé.
- Aucun payload désérialisé automatiquement.
- DOT modifiés uniquement parce que la roadmap replay/export évolue.
- Commentaires invisibles `ROADMAP_NOTE[phase2_2]` présents dans les DOT modifiés.
