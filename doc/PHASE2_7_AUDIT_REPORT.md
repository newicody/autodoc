# Phase 2.7 Audit — rapport de vérification

## Commandes exécutées

```bash
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
cd doc && make -f makefile
```

## Résultat

```text
63 passed
main.py exit code: 0
DOT_OK
```

## Inspection

- Aucun import OpenVINO réel dans `src`.
- Aucun import Qdrant ou SQLite dans le kernel.
- Le chemin d'inférence reste derrière `InferenceAdapter` + `BackendRegistry`.
- `OpenVINOBackend` reste contractuel et utilise un runtime injecté.
- Le replay reste hors Scheduler vivant.
- Les DOT ne sont pas modifiés pendant cette phase.

## Modifications proposées

Modifications documentaires uniquement :

- `README.md` : état du projet et commandes de validation.
- `.gitignore` : éviter de versionner caches Python et sorties locales.
- `doc/ARCHITECTURE_LAYERS.md` : état Phase 2.6 auditée.
- `doc/PROJECT_REVIEW_PHASE2_6.md` : analyse du modèle actuel.
- `doc/OPENVINO_MODEL_STRATEGY.md` : stratégie avant choix des modèles.
- `doc/CHANGELOG_PHASE2_7_AUDIT.md` : changelog de cette phase.
- `code_rule.md` : précision du modèle actuel après Phase 2.6.

Fichier de test inclus par sécurité :

- `tests/docs/test_dot_links.py` : version souple de vérification des liens DOT, sans règle canonique rigide.

## Décision OpenVINO

On est à l'étape juste avant l'intégration réelle.

La recommandation est de commencer par un backend d'embedding OpenVINO, puis seulement ensuite un backend de génération.
