# Phase 3.6 — Test report

## Scope

Ajout d'un tokenizer déterministe de test, pure stdlib, pour valider le pipeline
embedding abstrait sans dépendance externe et sans modèle OpenVINO réel.

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultat

```text
compileall OK
120 passed in 1.28s
main.py exit code: 0
DOT_OK
```

## Notes DOT

Graphviz affiche des warnings connus :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Ces warnings existaient déjà et n'empêchent pas la génération des SVG. Aucun SVG
n'est inclus dans l'artefact.

## OpenVINO

OpenVINO n'est pas requis pour cette phase. Les tests restent unitaires et
fonctionnent sans runtime OpenVINO installé.

La prochaine phase d'intégration locale pourra demander :

```bash
python3 -c "import openvino as ov; print(ov.__version__)"
```

et un modèle IR local :

```text
model.xml
model.bin
```
