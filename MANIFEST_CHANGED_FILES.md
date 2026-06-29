# Manifest — Phase 1.6 changed files

Ce lot contient uniquement les fichiers modifiés ou ajoutés pour la Phase 1.6.

## Code

```text
src/contracts/event.py
src/contracts/policy.py
src/policy/__init__.py
src/policy/engine.py
src/kernel/scheduler.py
src/kernel/launcher.py
```

## Tests

```text
tests/policy/test_policy_engine.py
tests/kernel/test_scheduler_policy.py
tests/runtime/test_component_proxy.py
```

## Documentation

```text
doc/ARCHITECTURE_LAYERS.md
doc/CHANGELOG_PHASE1_6.md
PHASE1_6_TEST_REPORT.md
MANIFEST_CHANGED_FILES.md
```

## DOT roadmap

```text
doc/docs/architecture/00_global.dot
doc/docs/architecture/scheduler/10_scheduler.dot
doc/docs/architecture/tests/80_tests.dot
```

Chaque DOT modifié contient un commentaire invisible `ROADMAP_NOTE[phase1_6]`.

## Exclusions volontaires

```text
Aucun .svg
Aucun script de patch
Aucun backend OpenVINO
Aucun fichier Qdrant/SQLite/Knowledge
```
