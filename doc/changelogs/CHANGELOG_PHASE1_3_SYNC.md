# Changelog — Phase 1.3 sync

## Objectif

Connecter réellement le Scheduler au package `src/context/` extrait en Phase 1.3.

## Changements

- `src/kernel/scheduler.py`
  - importe maintenant `ContextEngine` depuis `context.engine` ;
  - ne dépend plus de l'ancien moteur contenu dans `kernel.context_engine`.

- `src/kernel/launcher.py`
  - enregistre explicitement `ContextRequestHandler` depuis `context.handlers` ;
  - garde le Scheduler comme orchestrateur, sans logique de lecture directe des composants.

- `src/kernel/context_engine.py`
  - devient un shim de compatibilité :

    ```python
    from context.engine import ContextEngine
    ```

- `tests/context/test_context_engine.py`
  - vérifie que le contexte passe par le chemin événementiel ;
  - enregistre explicitement `ContextRequestHandler`, comme le launcher.

## Architecture

Aucune modification DOT nécessaire.

Les DOT actuels décrivent déjà le chemin prévu :

```text
Scheduler
  -> ContextEngine
  -> ContextCollector
  -> CONTEXT_REQUEST
  -> Queue
  -> Dispatcher
  -> ContextRequestHandler
  -> ComponentProxy.context()
  -> CONTEXT_REPLY
  -> ContextReducer
  -> GlobalContextSnapshot
```

## Validation

```text
7 passed
main.py exit code: 0
```
