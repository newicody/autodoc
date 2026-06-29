# Manifest — Phase 1.3 sync

Cette livraison synchronise réellement le Scheduler avec le package `src/context/` déjà présent dans le dépôt.

Elle ne change pas la roadmap DOT : les graphes décrivent déjà le chemin cible `Scheduler -> ContextEngine -> ContextCollector -> CONTEXT_REQUEST -> Dispatcher -> ContextRequestHandler`.

## Fichiers modifiés

```text
src/kernel/scheduler.py
src/kernel/launcher.py
src/kernel/context_engine.py
tests/context/test_context_engine.py
doc/CHANGELOG_PHASE1_3_SYNC.md
```

## Non modifié

```text
Aucun SVG.
Aucun DOT.
Aucun script de patch.
Aucun fichier OpenVINO/Qdrant/SQLite.
```

## Raison

Le dépôt contenait déjà `src/context/`, mais `src/kernel/scheduler.py` utilisait encore `kernel.context_engine`.
Cette étape supprime la duplication active : `kernel/context_engine.py` devient un shim de compatibilité et le Scheduler utilise `context.engine.ContextEngine`.
