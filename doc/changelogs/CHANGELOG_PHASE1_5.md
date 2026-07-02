# Changelog — Phase 1.5

## Ajout

- Ajout de `src/inference/adapter.py`.
- Ajout de `InferenceAdapter` comme membrane entre `InferenceRequestHandler` et les backends concrets.
- Ajout de tests dédiés à la sélection de backend.
- Ajout d'un test de rejet explicite pour backend inconnu.

## Modification

- `InferenceRequestHandler` délègue maintenant à `InferenceAdapter` au lieu de parler directement à `DummyInferenceBackend`.
- `Launcher` assemble `DummyInferenceBackend -> InferenceAdapter -> InferenceRequestHandler`.
- `src/inference/__init__.py` exporte `InferenceAdapter`.
- `ARCHITECTURE_LAYERS.md` documente le Layer 5 comme actif en Phase 1.5.
- `00_global.dot`, `scheduler/10_scheduler.dot`, `inference/40_inference.dot` et `tests/80_tests.dot` sont mis à jour avec commentaires invisibles `ROADMAP_NOTE[phase1_5]`.

## Décisions maintenues

- Le Scheduler ne connaît pas l'inférence.
- Le Dispatcher ne connaît pas les backends.
- Le handler ne connaît plus le backend fictif directement.
- OpenVINO reste futur.
- Le résultat d'inférence revient au composant par `Request.reply`.
- `INFERENCE_RESULT` reste une publication observable sur l'EventBus.
- Un backend inconnu provoque une erreur explicite plutôt qu'un fallback implicite.

## Validation

Commandes exécutées :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
```

Résultat attendu :

```text
12 passed
main.py exit code: 0
```
