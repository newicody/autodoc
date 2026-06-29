# Phase 3.9 — Test report — E5 CLI

## Objet

Ajout d'un point d'entrée CLI de développement pour exécuter le pipeline local
`multilingual-e5-small` depuis le terminal, sans script temporaire.

## Commandes exécutées dans le sandbox

```bash
PYTHONPATH=src python3 -m compileall -q src tests tools
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultats

```text
compileall OK
133 passed, 1 skipped in 0.74s
main.py exit code: 0
DOT_OK
```

Le warning Graphviz suivant reste connu et non bloquant :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

## Test réel OpenVINO local utilisateur

Le test local E5/OpenVINO a été validé côté utilisateur avant cette phase :

```text
pytest -q tests/integration/test_openvino_e5_local.py
1 passed in 4.96s
```

## Fichiers runtime modifiés

```text
src/inference/e5_cli.py
src/inference/__init__.py
tools/embed_e5.py
```

## Garanties

- Aucun changement Scheduler.
- Aucun changement Dispatcher.
- Aucun changement ComponentProxy.
- Aucun changement PolicyEngine.
- Aucun Qdrant.
- Aucun SVG inclus.
- Aucun script de patch.
- Le CLI est testé avec un builder injecté, donc la suite portable ne dépend pas d'OpenVINO réel.
