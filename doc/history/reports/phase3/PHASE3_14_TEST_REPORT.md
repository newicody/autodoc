# PHASE 3.14 TEST REPORT — E5 search report

## But

Ajouter un rapport de recherche E5 local qui affiche, pour chaque résultat :

- score ;
- id ;
- fichier source si disponible ;
- lignes source si disponibles ;
- index de chunk ;
- extrait stable ;
- sortie JSON exploitable.

## Validations exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py
tools/search_e5_corpus.py --help
```

## Résultats

```text
compileall OK
179 passed, 1 skipped in 1.11s
main.py exit code: 0
DOT_OK
DOT links: 3 passed
search_e5_corpus.py --help OK
```

## Note Graphviz

`dot` affiche encore des avertissements Graphviz connus :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Ces avertissements sont préexistants et ne bloquent pas la génération SVG locale. Aucun SVG n'est inclus dans le lot.

## Test OpenVINO réel

Non relancé dans le sandbox. La phase ne modifie pas le pipeline OpenVINO réel : elle modifie uniquement la projection des résultats du corpus local. Le test réel E5 reste à lancer localement si besoin :

```bash
MISSIPY_RUN_OPENVINO_LOCAL=1 \
MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
pytest -q tests/integration/test_openvino_e5_local.py
```
