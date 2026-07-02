# Changelog — Phase 1.4

## Ajout

- Ajout du package `src/inference/`.
- Ajout de `DummyInferenceBackend`.
- Ajout de `InferenceRequestHandler`.
- Ajout de tests dédiés à l'inférence fictive.
- Ajout du graphe `doc/docs/architecture/inference/40_inference.dot`.

## Modification

- `contracts.inference` devient un contrat réellement exploité par le runtime.
- `Launcher` enregistre maintenant `InferenceRequestHandler` dans le `Dispatcher`.
- `ARCHITECTURE_LAYERS.md` documente le Layer 5 comme actif en Phase 1.4.
- `00_global.dot`, `scheduler/10_scheduler.dot` et `tests/80_tests.dot` sont mis à jour avec commentaires invisibles `ROADMAP_NOTE[phase1_4]`.

## Décisions maintenues

- Le Scheduler ne connaît pas le backend d'inférence.
- OpenVINO reste futur.
- Le résultat d'inférence revient au composant par `Request.reply`.
- Un `INFERENCE_RESULT` est publié sur l'EventBus uniquement pour observation.
- `DummyInferenceBackend` doit rester disponible comme backend de test permanent.

## Validation

Commandes exécutées :

```bash
python3 -m compileall -q src tests
pytest -q
python3 src/main.py
```

Résultat attendu :

```text
10 passed
main.py exit code: 0
```
