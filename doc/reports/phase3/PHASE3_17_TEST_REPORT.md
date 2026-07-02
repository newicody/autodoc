# PHASE3_17_TEST_REPORT

## Phase

Phase 3.17 — E5 build lock.

## Objectif

Empêcher deux reconstructions concurrentes de viser le même corpus E5 local.

La Phase 3.16 protège le remplacement final avec `write_atomic()`. La Phase 3.17 ajoute un verrou fichier pendant toute la phase longue de build/reuse/embedding.

## Commandes exécutées

```bash
find . -type d -name __pycache__ -exec rm -rf {} +
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
PYTHONPATH=src ./tools/build_e5_corpus.py --help
PYTHONPATH=src ./tools/search_e5_corpus.py --help
```

## Résultats

```text
compileall OK
194 passed, 1 skipped in 0.94s
main.py exit code: 0
DOT_OK
build_e5_corpus.py --help OK
search_e5_corpus.py --help OK
```

Graphviz a conservé l'avertissement connu :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Cet avertissement n'empêche pas la génération ni la validation des DOT.

## Points testés

- `E5CorpusBuildLock` crée un fichier de lock voisin de la cible.
- Le lock est écrit avec un schéma inspectable `missipy.e5.corpus.lock.v1`.
- Le lock est supprimé à la libération normale.
- Le lock est supprimé en sortie de contexte même si une exception survient.
- Un lock déjà présent bloque un second build.
- La CLI `build_e5_corpus.py` active le verrou par défaut.
- La CLI expose `--no-lock` pour développement contrôlé.
- La sortie de build affiche `lock_enabled` et `lock_path`.

## Non-régressions

- Aucun changement Scheduler.
- Aucun changement Qdrant.
- Aucun changement OpenVINO runtime.
- Aucun changement du schéma corpus `missipy.e5.corpus.v1`.
- Aucun SVG inclus dans l'artefact.
