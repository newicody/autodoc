# Changelog — Phase 2.2

## Objectif

Ajouter un export déterministe de `ReplayReport`, sans connecter le replay au Scheduler vivant.

## Ajouté

- `contracts.replay.ReplayReportExport`
- `observability.replay_exporter.ReplayReportExporter`
- export texte stable via `ReplayReport.to_lines()`
- export JSON compact et déterministe avec `json.dumps(..., sort_keys=True, separators=(",", ":"))`
- tests unitaires d'export texte, JSON et validation du contrat d'export

## Contraintes respectées

- pas de dépendance externe ;
- pas de SVG généré ;
- pas de script de patch ;
- aucun accès au Scheduler ;
- aucun `Event` vivant dans l'export ;
- aucun `Future` capturé ;
- aucune désérialisation automatique de `payload_repr` ;
- sortie déterministe comparable en test.

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

## Validation

```text
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

Résultat attendu :

```text
42 passed
main.py exit code: 0
```

## Étape suivante

Phase 2.3 : écriture contrôlée des exports texte/JSON vers fichiers, avec chemins explicites et toujours hors Scheduler vivant.
