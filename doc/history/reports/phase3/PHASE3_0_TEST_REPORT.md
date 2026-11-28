# Phase 3.0 — Test report

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultats

```text
78 passed in 0.86s
main.py exit code: 0
DOT_OK
```

Graphviz émet l'avertissement connu suivant sur certains graphes avec `splines=ortho` et labels d'arêtes :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Cet avertissement n'empêche pas la génération des SVG et ne signale pas une erreur de lien DOT.

## Vérifications spécifiques Phase 3.0

- `OpenVINOModelProfile` valide `embedding`, `generation` et `raw`.
- Les profils rejettent les tâches inconnues.
- Les métadonnées de profil sont copiées puis exposées en lecture seule.
- `OpenVINOModelProfileRegistry` sélectionne explicitement un profil par nom.
- Le registre de profils n'a pas de fallback implicite.
- `OpenVINOModelProfile.to_backend_config()` produit une `OpenVINOBackendConfig` compatible avec les phases précédentes.
- Aucun import `openvino` n'a été ajouté hors `src/inference/openvino_runtime.py`.
- Aucun changement Scheduler / Dispatcher / ComponentProxy.
