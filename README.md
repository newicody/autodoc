# Phase 5.8 — E5 ContextEngine manual CLI intake

Cette archive ajoute une bordure CLI locale autour des contrats déjà posés en 5.6 et 5.7.

La chaîne visée :

```text
artifact-dir Phase 4
-> ContextEngine.attach_e5_artifact_dir()
-> inspect_e5_context_engine()
-> sortie text/json
```

## Usage

```bash
PYTHONPATH=src python3 -m context.e5_context_engine_cli /tmp/autodoc_e5_dry_run
PYTHONPATH=src python3 -m context.e5_context_engine_cli --format json /tmp/autodoc_e5_dry_run
```

Options utiles :

```text
--component-name NAME
--priority INT
--include-context-text
--hide-prompt-text
--require-ready
--format text|json
```

## Ce que ça ne fait pas

```text
pas d'autoload E5
pas de Scheduler vivant
pas de daemon
pas de réseau
pas d'API GitHub
pas de token
pas de polling
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

Cette CLI construit un `ContextEngine` éphémère pour vérifier l'intake local ; elle ne modifie pas le micro-kernel vivant.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Application

Extraire l'archive à la racine du dépôt :

```bash
tar -xzf autodoc_phase5_8_e5_context_engine_cli.tar.gz
```

## Tests recommandés

```bash
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_cli.py
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_status.py
PYTHONPATH=src pytest -q tests/context/test_e5_context_engine_intake.py
PYTHONPATH=src pytest -q tests/context/test_context_engine.py::test_context_engine_uses_event_path_for_snapshot
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q

PYTHONPATH=src python3 -m context.e5_context_engine_cli --help
```
