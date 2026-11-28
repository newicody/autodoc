# Phase 3.18 — Test report

## Scope

Phase 3.18 ajoute une commande de rebuild sûr du corpus E5 local : staging, validation optionnelle et promotion finale vers l'index cible.

## Validations exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
./tools/rebuild_e5_corpus.py --help
./tools/build_e5_corpus.py --help
./tools/search_e5_corpus.py --help
find doc/docs/architecture -name '*.dot' -print0 | xargs -0 -I{} dot -Tsvg {} -o /tmp/phase318.svg
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py

Phase 3.18 test report

Commands run:

- git status --short
- PYTHONPATH=src pytest -q tests/rules
- PYTHONPATH=src pytest -q
- PYTHONPATH=src pytest -q tests/integration/test_openvino_e5_local.py

Results:

- tests/rules: 4 passed in 0.19s
- full portable suite: 203 passed, 1 skipped in 0.74s
- OpenVINO E5 local integration test: 1 skipped in 0.05s

Notes:

- Scheduler/domain boundary rule is green.
- Portable suite is green.
- OpenVINO E5 local pytest was skipped in this run.
- No Qdrant change.
- No corpus format change.
- No Scheduler functional change beyond justified boundary correction if applicable.
- No SVG.
- No patch script.

Statut avant Phase 4

Tu peux fermer 3.18 si :

git status --short

ne sort rien, ou seulement les fichiers de clôture attendus.

Verdict :

Phase 3.18 portable: OK
Phase 3.18 OpenVINO pytest local: skipped
Phase 3.18 manual E5 local: déjà validé précédemment
Phase 4: autorisée après commit propre de clôture
```

## Résultats

```text
compileall OK
203 passed, 1 skipped in 0.81s
main.py exit code: 0
rebuild_e5_corpus.py --help OK
build_e5_corpus.py --help OK
search_e5_corpus.py --help OK
DOT_OK
DOT links: 3 passed
```

## Note Graphviz

Graphviz émet l'avertissement connu :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Ce warning existait déjà et ne bloque pas la génération DOT/SVG.

## Hors périmètre

- Aucun SVG inclus.
- Aucun script de patch.
- Aucun changement Scheduler.
- Aucun Qdrant.
