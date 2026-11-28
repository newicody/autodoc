# CHANGELOG — Phase 1.6

## Ajouté

- `src/policy/engine.py`
  - `PolicyConfig`
  - `PolicyEngine`
- `src/policy/__init__.py`
- `EventType.POLICY_DENIED`
- `Decision.allow()` et `Decision.deny()` dans `contracts.policy`
- Tests policy :
  - source obligatoire ;
  - budget de priorité ;
  - `SHUTDOWN` réservé au kernel ;
  - destination composant enregistrée ;
  - modèle d'inférence autorisé/refusé ;
  - publication observable `POLICY_DENIED` ;
  - retour `Decision` au composant via `Request.reply`.

## Modifié

- `Scheduler.emit()` délègue maintenant l'autorisation à `PolicyEngine` avant `PriorityQueue.put()`.
- En cas de refus, le Scheduler :
  - ne queue pas l'événement ;
  - publie `POLICY_DENIED` sur `EventBus` ;
  - résout `Request.reply` avec une `Decision(allowed=False)`.
- `Launcher` instancie explicitement `PolicyEngine` et l'injecte dans `Scheduler`.
- Test d'événement inconnu ajusté pour ne pas se confondre avec les règles spécifiques `INFERENCE_REQUEST`.

## DOT modifiés

- `doc/docs/architecture/00_global.dot`
- `doc/docs/architecture/scheduler/10_scheduler.dot`
- `doc/docs/architecture/tests/80_tests.dot`

Chaque fichier DOT modifié contient un commentaire invisible `ROADMAP_NOTE[phase1_6]` expliquant la raison architecturale du changement.

## Non modifié

- Aucun SVG.
- Aucun script de patch.
- Aucun backend OpenVINO.
- Aucun changement Qdrant / SQLite / Knowledge.

## Validation

```text
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 src/main.py
```

Résultat :

```text
20 passed
main.py exit code: 0
```
