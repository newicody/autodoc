# Phase 5.7 — E5 ContextEngine status projection

Cette archive ajoute une projection passive de l'état E5 attaché au `ContextEngine`.

La chaîne devient observable sans déclencher d'effet de bord :

```text
ContextEngine.current_inference_context
+ last_snapshot optionnel
-> E5ContextEngineStatus
-> to_json_dict() / to_text()
```

## Usage

```python
from context.e5_context_engine_status import inspect_e5_context_engine

status = inspect_e5_context_engine(engine)
print(status.to_text())
```

Ou directement depuis un `InferenceContext` :

```python
from context.e5_context_engine_status import inspect_e5_inference_context

status = inspect_e5_inference_context(inference_context)
payload = status.to_json_dict()
```

## Ce que ça ne fait pas

```text
pas de lecture de fichiers
pas de mutation du contexte
pas d'autoload E5
pas de Scheduler vivant
pas de daemon
pas de réseau
pas d'API GitHub
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Application

Extraire l'archive à la racine du dépôt :

```bash
tar -xzf autodoc_phase5_7_e5_context_engine_status.tar.gz
```

## Tests recommandés

```bash
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_status.py
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_intake.py
PYTHONPATH=src pytest -q tests/context/test_context_engine.py::test_context_engine_uses_event_path_for_snapshot
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```
