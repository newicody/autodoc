# CHANGELOG Phase 2.4 — Replay bundle + navigation DOT

## Objectif

Cette phase ajoute un format de dossier replay contrôlé et corrige la navigation
DOT descendante/remontante autour du scheduler.

## Ajouts code

- `src/observability/replay_bundle.py`
  - `ReplayReportBundleWriter`
  - écrit `report.txt`, `report.json` et `manifest.json`
  - utilise uniquement `ReplayReportExporter` et `ReplayReportFileWriter`
  - ne connaît pas le Scheduler
  - ne publie aucun événement
  - n'écrase aucun fichier sans `overwrite=True`
  - ne crée aucun répertoire sans `create_parents=True`

## Contrats

- `ReplayBundleWriteResult`
  - décrit le dossier généré
  - expose les fichiers écrits
  - expose le manifeste
  - expose `total_bytes_written`
  - expose `sha256_by_path`

## Documentation DOT

Correction de liens descendants manquants :

- `scheduler/dispatcher/11_dispatcher.dot`
- `scheduler/event_bus/12_event_bus.dot`
- `scheduler/priority_queue/13_priority_queue.dot`
- `scheduler/component_proxy/14_component_proxy.dot`

Ces fichiers ferment les liens déjà présents dans `scheduler/10_scheduler.dot` et
`inference/40_inference.dot`.

## Test ajouté

- `tests/docs/test_dot_links.py`
  - vérifie que chaque `URL="*.svg"` dans les fichiers DOT pointe vers une
    source DOT existante.
  - le test ne dépend pas des SVG générés par le makefile.

## Validation

```text
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
dot -Tsvg <chaque fichier DOT> >/dev/null
```

Résultat :

```text
52 passed
main.py exit code: 0
DOT_OK
```
