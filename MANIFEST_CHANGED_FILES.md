# Manifest — Phase 2.0 changed files

## Ajoutés

```text
src/observability/replay_sandbox.py
tests/observability/test_replay_sandbox.py
doc/CHANGELOG_PHASE2_0.md
PHASE2_0_TEST_REPORT.md
MANIFEST_CHANGED_FILES.md
```

## Modifiés

```text
src/contracts/replay.py
src/observability/__init__.py
doc/ARCHITECTURE_LAYERS.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/observability/70_observability.dot
doc/docs/architecture/tests/80_tests.dot
```

## Non inclus

```text
*.svg
scripts de patch
```

## Raison des DOT modifiés

Les DOT sont une roadmap vivante. Ils ont été modifiés uniquement parce que la Phase 2.0 ajoute un élément architectural réel :

```text
ReplayPlan -> ReplaySandbox -> ReplaySandboxResult
```

Commentaires invisibles ajoutés :

```text
ROADMAP_NOTE[phase2_0]
```
