# Phase 5.9 — E5 ContextEngine CLI report file

Cette archive étend la bordure CLI manuelle de la Phase 5.8 sans créer une nouvelle surface de commande.

La chaîne visée reste :

```text
artifact-dir Phase 4
-> ContextEngine.attach_e5_artifact_dir()
-> inspect_e5_context_engine()
-> payload missipy.e5.context_engine_cli.v1
-> stdout text/json
-> report JSON atomique optionnel
```

## Usage

```bash
PYTHONPATH=src python3 -m context.e5_context_engine_cli \
  --report-file /tmp/e5_context_engine_status.json \
  /tmp/autodoc_e5_dry_run

PYTHONPATH=src python3 -m context.e5_context_engine_cli \
  --format json \
  --report-file /tmp/e5_context_engine_status.json \
  /tmp/autodoc_e5_dry_run
```

`--report-file` persiste le même payload JSON que la sortie `--format json` :

```text
schema: missipy.e5.context_engine_cli.v1
intake: missipy.e5.context_engine_intake.v1
status: missipy.e5.context_engine_status.v1
```

## Frontière IO

L'écriture fichier est volontairement limitée à la CLI :

```text
context.e5_context_engine_cli
-> _write_report()
-> fichier JSON atomique
```

Le domaine, le `ContextEngine`, le runtime E5 et les contrats d'attachement ne savent pas écrire ce fichier.

## Ce que ça ne fait pas

```text
pas de nouvelle CLI
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

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Application

Extraire l'archive à la racine du dépôt :

```bash
tar -xzf autodoc_phase5_9_e5_context_engine_cli_report.tar.gz
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
