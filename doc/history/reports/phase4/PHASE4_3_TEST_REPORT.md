# Phase 4.3 — Test report

## Scope

Phase 4.3 ajoute un garde-fou de score minimal optionnel à la recherche E5 locale.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes à exécuter après extraction

```bash
PYTHONPATH=src pytest -q tests/inference
```

```bash
PYTHONPATH=src pytest -q tests/rules
```

```bash
PYTHONPATH=src pytest -q
```

```bash
git status --short
```

## Validations attendues

- `E5CorpusSearcher.search(..., min_score=...)` filtre les scores trop faibles.
- Un hit avec `score == min_score` est conservé.
- Une recherche peut retourner `hit_count: 0` lorsque tous les hits sont sous le seuil.
- La CLI accepte `--min-score FLOAT`.
- La CLI rejette un score hors intervalle `[-1.0, 1.0]` avec code `2`.
- La sortie texte respecte le filtrage.
- La sortie JSON respecte le filtrage.
- Les graphes DOT Phase 4.3 passent une génération Graphviz locale.

## Exemple CLI

```bash
PYTHONPATH=src ./tools/search_e5_corpus.py \
  --index /tmp/autodoc_e5_corpus.json \
  --limit 5 \
  --min-score 0.86 \
  "rebuild sûr avec staging validation promotion"
```

## Résultats locaux

À compléter après exécution dans le clone local.

```text
PYTHONPATH=src pytest -q tests/inference
<coller le résultat>

PYTHONPATH=src pytest -q tests/rules
<coller le résultat>

PYTHONPATH=src pytest -q
<coller le résultat>
```

## Verdict attendu

```text
Phase 4.3 local score guard: OK
Phase 4.3 CLI --min-score: OK
Phase 4.3 text output filtering: OK
Phase 4.3 JSON output filtering: OK
Phase 4.3 corpus format unchanged: OK
```

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- DOT sources mis à jour pour la roadmap inference.
- Aucun SVG versionné.
- Aucun script de patch.


## Graphes DOT

Commandes de vérification possibles :

```bash
dot -Tsvg doc/docs/architecture/inference/52_e5_search_report.dot >/tmp/52_e5_search_report.svg
dot -Tsvg doc/docs/architecture/inference/57_e5_score_guard.dot >/tmp/57_e5_score_guard.svg
rm -f /tmp/52_e5_search_report.svg /tmp/57_e5_score_guard.svg
```

Les SVG générés ne doivent pas être ajoutés au dépôt.
