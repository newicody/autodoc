# Phase 4.6 — Test report

## Scope

Phase 4.6 ajoute un diagnostic local du corpus E5 JSON.

La phase reste hors Scheduler, hors Qdrant et conserve le format corpus existant.

## Commandes à exécuter

```bash
PYTHONPATH=src pytest -q tests/inference
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

Validation DOT source :

```bash
dot -Tsvg doc/docs/architecture/inference/59_e5_source_hygiene_cli.dot >/tmp/59_e5_source_hygiene_cli.svg
dot -Tsvg doc/docs/architecture/inference/60_e5_corpus_diagnostics.dot >/tmp/60_e5_corpus_diagnostics.svg
rm -f /tmp/59_e5_source_hygiene_cli.svg /tmp/60_e5_corpus_diagnostics.svg
```

## Résultats attendus

```text
tests/inference : passed
tests/rules     : passed
suite complète  : passed, 1 skipped attendu si OpenVINO local non activé
```

## Validations couvertes

- diagnostic de schéma/modèle/backend/tokenizer/dimension ;
- compte des chunks ;
- compte des sources ;
- répartition par extension ;
- sources dominantes stables ;
- compte `embedding_reused` true/false/inconnu ;
- détection de métadonnées `source_path` manquantes ;
- sortie texte ;
- sortie JSON ;
- validation de `--top-sources-limit` ;
- lecture seule via `E5CorpusJsonStore.read()`.

## Hors périmètre

- Aucun Scheduler.
- Aucun Qdrant.
- Aucun changement de format corpus.
- Aucun SVG versionné.
- Aucun script de patch.
