# Phase 4.2 — Test report

## Scope

Phase 4.2 valide la recherche E5 locale dev-ready sur le corpus réel du dépôt.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes exécutées

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py --help
```

```bash
PYTHONPATH=src ./tools/rebuild_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --source-dir . \
  --chunk-chars 1200 \
  --validation-query "rebuild sûr avec staging validation promotion"
```

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  "rebuild sûr avec staging validation promotion"
```

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  "Scheduler telemetry boundary code_rule"
```

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  "rapport de recherche avec source lignes extrait"
```

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 3 \
  --format json \
  "OpenVINO multilingual-e5-small local"
```

## Résultats rebuild

```text
index: /tmp/autodoc_e5_corpus.json
staging: /tmp/.autodoc_e5_corpus.json.rebuild.json
promoted: True
model: openvino.embedding.e5-small
backend: openvino.embedding.e5-small
tokenizer: transformers.multilingual-e5-small
dimension: 384
size: 218
atomic_write: True
lock_enabled: True
validation_search: True
validation_hit_count: 1
validation_best_score: 0.87834898
```

## Résultats recherche

### Requête rebuild sûr

Meilleurs résultats :

```text
PHASE3_18_TEST_REPORT.md
doc/ARCHITECTURE_LAYERS.md
README.md
doc/CHANGELOG_PHASE3_18_E5_SAFE_REBUILD.md
doc/MODEL_E5_SAFE_REBUILD_PHASE3_18.md
```

### Requête Scheduler / telemetry / code_rule

Meilleurs résultats :

```text
PHASE3_18_TEST_REPORT.md
README.md
doc/CHANGELOG_PHASE1_7.md
doc/ARCHITECTURE_LAYERS.md
doc/CHANGELOG_PHASE3_9_E5_CLI.md
```

### Requête rapport source/lignes/extrait

Meilleurs résultats :

```text
doc/CHANGELOG_PHASE3_14_E5_SEARCH_REPORT.md
doc/MODEL_E5_SEARCH_REPORT_PHASE3_14.md
PHASE3_14_TEST_REPORT.md
doc/CHANGELOG_PHASE3_14_E5_SEARCH_REPORT.md
README.md
```

### Requête OpenVINO multilingual-e5-small local

Meilleurs résultats JSON :

```text
doc/ARCHITECTURE_LAYERS.md
PHASE3_8_TEST_REPORT.md
doc/MODEL_E5_LOCAL_PHASE3_7.md
```

## Verdict

```text
Phase 4.2 local rebuild: OK
Phase 4.2 local text search: OK
Phase 4.2 local JSON search: OK
Phase 4.2 source/lines/excerpt report: OK
Phase 4.2 corpus format unchanged: OK
```

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun DOT.
- Aucun SVG.
- Aucun script de patch.
